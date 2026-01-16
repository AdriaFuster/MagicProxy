import os
import re
import requests
import time
import torch
import numpy as np
import urllib.request
from bs4 import BeautifulSoup
from PIL import Image
from spandrel import ModelLoader

def executar_pas1(archivo_cartas, carpeta_base, executar_upscale, callback=None):
    """
    Funció principal per descarregar cartes i fer upscale.
    Informa del progrés a través de la funció 'callback'.
    """
    
    def log_update(missatge, progrés=None):
        if callback:
            # Enviem el missatge a la consola i el progrés a la barra
            callback(progrés, missatge)
        else:
            print(missatge)

    # 1. Definició de rutes
    carpeta_originales = os.path.join(carpeta_base, "cartas")
    carpeta_4k = os.path.join(carpeta_base, "cartas_4k")
    archivo_informe = os.path.join(carpeta_base, "informe_recerca.txt")

    os.makedirs(carpeta_originales, exist_ok=True)
    if executar_upscale:
        os.makedirs(carpeta_4k, exist_ok=True)

    # 2. Configuració del Model Real-ESRGAN
    model = None
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if executar_upscale:
        MODEL_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
        MODEL_PATH = "RealESRGAN_x4plus.pth"

        if not os.path.exists(MODEL_PATH):
            log_update("⬇️ Descarregant model Real-ESRGAN x4 (només el primer cop)...", 0.05)
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

        log_update("⚙️ Carregant model a la memòria...", 0.1)
        loader = ModelLoader()
        model = loader.load_from_file(MODEL_PATH)
        model.to(device)
        model.eval()

    # --- Funcions auxiliars internes ---
    def upscale_image_from_path(input_path, output_path):
        img = Image.open(input_path).convert("RGB")
        img_np = np.array(img)
        tensor = torch.from_numpy(img_np).permute(2, 0, 1).float().div(255).unsqueeze(0).to(device)
        with torch.no_grad():
            out = model(tensor)
        out_img = out.squeeze(0).permute(1, 2, 0).clamp(0, 1).cpu().numpy()
        out_img = (out_img * 255).astype(np.uint8)
        Image.fromarray(out_img).save(output_path, format="WEBP")

    def normalizar_nombre(nombre):
        if "//" in nombre:
            nombre = nombre.split("//")[1]
        return nombre.strip()

    def formatear_nombre_url(nombre):
        nombre = nombre.lower()
        nombre = re.sub(r'[^a-z0-9\s-]', '', nombre)
        return nombre.replace(' ', '-')

    def generar_url_gatherer(nombre_url, set_url, numero_url):
        return f"https://gatherer.wizards.com/{set_url}/es-es/{numero_url}/{nombre_url}"

    def obtener_oracle_id(nombre):
        r = requests.get("https://api.scryfall.com/cards/named", params={"exact": nombre})
        if r.status_code != 200: return None
        return r.json().get("oracle_id")

    def obtener_todos_prints(oracle_id):
        if not oracle_id: return []
        url = "https://api.scryfall.com/cards/search"
        params = {"q": f"oracleid:{oracle_id}", "unique": "prints"}
        resultados = []
        vistos = set()
        while url:
            r = requests.get(url, params=params)
            if r.status_code != 200: break
            data = r.json()
            for carta in data.get("data", []):
                set_code = carta["set"].upper()
                numero = re.sub(r'\D', '', carta["collector_number"])
                if (set_code, numero) not in vistos:
                    vistos.add((set_code, numero))
                    resultados.append((set_code, numero))
            url = data.get("next_page")
            params = None
            time.sleep(0.1)
        return resultados

    def buscar_imagen_en_url(url):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200: return None
            soup = BeautifulSoup(r.text, 'html.parser')
            img = soup.find('img', {'data-testid': 'cardFrontImage'})
            return img.get('src') if img else None
        except:
            return None

    # --- Inici del procés ---
    try:
        with open(archivo_cartas, 'r', encoding='utf-8') as f:
            lineas = [l.strip() for l in f.readlines() if l.strip()]
    except Exception as e:
        log_update(f"❌ Error llegint l'arxiu: {e}")
        return

    total_lineas = len(lineas)
    log_update(f"📦 Mazo detectat: {total_lineas} cartes diferents.")

    with open(archivo_informe, 'w', encoding='utf-8') as info:
        info.write("INFORME D'EXCEPCIONS I ERRORS DE RECERCA\n")
        info.write("="*40 + "\n\n")

        for idx, linea in enumerate(lineas):
            percentatge = (idx + 1) / total_lineas
            try:
                # Parsing de la línia
                n_cartas_str, resto = linea.split(' ', 1)
                n_cartas = int(n_cartas_str)
                nombre_set, numero_carta = resto.rsplit(' ', 1)
                nombre_raw, set_raw = re.match(r'(.+?)\s+\((\w+)\)', nombre_set).groups()
                
                nombre = normalizar_nombre(nombre_raw)
                log_update(f"🔍 Cercant: {nombre}...", percentatge)
                
                nombre_url = formatear_nombre_url(nombre)
                set_url = set_raw.upper()
                numero_url = re.sub(r'\D', '', numero_carta)

                links_intentats = []
                img_url = None
                metode = ""

                # 1. Intentar Link Original
                url_original = generar_url_gatherer(nombre_url, set_url, numero_url)
                img_url = buscar_imagen_en_url(url_original)
                
                if img_url:
                    metode = "ORIGINAL"
                else:
                    links_intentats.append(url_original)
                    oracle_id = obtener_oracle_id(nombre)
                    prints_alternatius = obtener_todos_prints(oracle_id)
                    
                    for set_alt, num_alt in prints_alternatius:
                        url_alt = generar_url_gatherer(nombre_url, set_alt, num_alt)
                        if url_alt not in links_intentats:
                            links_intentats.append(url_alt)
                            img_url = buscar_imagen_en_url(url_alt)
                            if img_url:
                                metode = "ALTERNATIVA"
                                break
                
                # Informe
                if not img_url:
                    info.write(f"CARTA: {nombre}\nESTAT: ❌ NO TROBADA\nLINKS: {links_intentats}\n\n")

                if img_url:
                    img_data = requests.get(img_url).content
                    for i in range(1, n_cartas + 1):
                        suffix = "" if n_cartas == 1 else f"_{i}"
                        filename = f"{nombre.lower().replace(' ', '_')}{suffix}.webp"
                        ruta_original = os.path.join(carpeta_originales, filename)
                        
                        with open(ruta_original, "wb") as f_img:
                            f_img.write(img_data)
                        
                        if executar_upscale:
                            log_update(f"✨ Millorant qualitat: {nombre}...", percentatge)
                            ruta_4k_file = os.path.join(carpeta_4k, filename)
                            upscale_image_from_path(ruta_original, ruta_4k_file)

            except Exception as e:
                log_update(f"⚠️ Error processant línia: {linea} -> {e}")

    log_update("✅ Pas 1 finalitzat amb èxit!", 1.0)