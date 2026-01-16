import os
import torch
import numpy as np
from PIL import Image
from spandrel import ModelLoader
import urllib.request

def executar_upscale_folder(input_folder, output_folder, callback=None):
    def log(p, m):
        if callback: callback(p, m)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_path = "RealESRGAN_x4plus.pth"
    model_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if not os.path.exists(model_path):
        log(0.1, "Descarregant model Real-ESRGAN x4...")
        urllib.request.urlretrieve(model_url, model_path)

    log(0.2, f"🚀 Carregant model en {device}...")
    loader = ModelLoader()
    model = loader.load_from_file(model_path).to(device).eval()

    files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    total = len(files)

    if total == 0:
        log(0, "❌ No s'han trobat imatges a la carpeta d'origen.")
        return

    for idx, filename in enumerate(files):
        progresso = 0.2 + (idx / total) * 0.8
        log(progresso, f"Processant ({idx+1}/{total}): {filename}")
        
        try:
            image_path = os.path.join(input_folder, filename)
            img = Image.open(image_path).convert("RGB")
            img_tensor = torch.from_numpy(np.array(img)).permute(2, 0, 1).float().div(255).unsqueeze(0).to(device)

            with torch.no_grad():
                output_tensor = model(img_tensor)
            
            output_img = output_tensor.squeeze(0).permute(1, 2, 0).clamp(0, 1).cpu().numpy()
            output_img = (output_img * 255).astype(np.uint8)
            
            Image.fromarray(output_img).save(os.path.join(output_folder, filename))
        except Exception as e:
            log(progresso, f"❌ Error en {filename}: {e}")

    log(1.0, f"✨ Acabat! Revisa: {output_folder}")