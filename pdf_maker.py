import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors

def generar_pdf_final(input_folder, output_pdf, callback=None):
    """
    Funció per convertir les imatges d'una carpeta en un PDF maquetat per a Magic.
    Informa del progrés a través de callback.
    """
    def log(p, m):
        if callback: callback(p, m)
        else: print(m)

    # --- CONFIGURACIÓ DE MIDES ---
    CARD_WIDTH = 63 * mm
    CARD_HEIGHT = 88 * mm
    GAP = 2 * mm 
    LINE_OFFSET = 0.5 * mm 
    COLS = 3
    ROWS = 3
    EXTENSIONS = (".webp", ".png", ".jpg", ".jpeg")

    # Càlculs de la graella
    GRID_WIDTH = (COLS * CARD_WIDTH) + ((COLS - 1) * GAP)
    GRID_HEIGHT = (ROWS * CARD_HEIGHT) + ((ROWS - 1) * GAP)
    PAGE_WIDTH, PAGE_HEIGHT = A4
    OFFSET_X = (PAGE_WIDTH - GRID_WIDTH) / 2
    OFFSET_Y = (PAGE_HEIGHT - GRID_HEIGHT) / 2

    # --- FUNCIONS INTERNES DE DIBUIX ---
    def draw_guides_displaced(c):
        c.setStrokeColor(colors.green) 
        c.setLineWidth(0.1 * mm)
        for col in range(COLS):
            for row in range(ROWS):
                x = OFFSET_X + (col * (CARD_WIDTH + GAP))
                y = OFFSET_Y + (row * (CARD_HEIGHT + GAP))
                c.line(x - LINE_OFFSET, 0, x - LINE_OFFSET, PAGE_HEIGHT)
                c.line(x + CARD_WIDTH + LINE_OFFSET, 0, x + CARD_WIDTH + LINE_OFFSET, PAGE_HEIGHT)
                c.line(0, y - LINE_OFFSET, PAGE_WIDTH, y - LINE_OFFSET)
                c.line(0, y + CARD_HEIGHT + LINE_OFFSET, PAGE_WIDTH, y + CARD_HEIGHT + LINE_OFFSET)

    def draw_page_content(c, page_images, page_num):
        for idx, img_path in enumerate(page_images):
            col = idx % COLS
            row = ROWS - 1 - (idx // COLS)
            x = OFFSET_X + (col * (CARD_WIDTH + GAP))
            y = OFFSET_Y + (row * (CARD_HEIGHT + GAP))
            
            bleed = LINE_OFFSET + 1 * mm
            c.setFillColor(colors.black)
            c.rect(x - bleed, y - bleed, CARD_WIDTH + (bleed*2), CARD_HEIGHT + (bleed*2), fill=1, stroke=0)
            c.drawImage(img_path, x, y, width=CARD_WIDTH, height=CARD_HEIGHT)

        draw_guides_displaced(c)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        c.drawRightString(PAGE_WIDTH - 10*mm, 5*mm, f"Pàgina {page_num}")

    # --- EXECUCIÓ ---
    if not os.path.exists(input_folder):
        log(0, f"❌ La carpeta no existeix: {input_folder}")
        return

    images = sorted([os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith(EXTENSIONS)])

    if not images:
        log(0, f"❌ No s'han trobat imatges a: {input_folder}")
        return

    log(0.1, f"🚀 Generant PDF amb {len(images)} cartes...")
    
    c = canvas.Canvas(output_pdf, pagesize=A4)
    cards_per_page = COLS * ROWS
    total_pages = (len(images) + cards_per_page - 1) // cards_per_page

    for i in range(0, len(images), cards_per_page):
        page_num = (i // cards_per_page) + 1
        percentatge = page_num / total_pages
        
        log(percentatge, f"Creant pàgina {page_num} de {total_pages}...")
        
        page_images = images[i:i + cards_per_page]
        draw_page_content(c, page_images, page_num)
        c.showPage()
    
    c.save()
    log(1.0, f"✅ PDF creat correctament a: {os.path.basename(output_pdf)}")