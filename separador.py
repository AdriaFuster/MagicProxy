import os
from PyPDF2 import PdfReader, PdfWriter

def dividir_pdf(input_pdf, output_dir, callback=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)
    base_name = os.path.splitext(os.path.basename(input_pdf))[0]

    for i in range(total_pages):
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        output_path = os.path.join(output_dir, f"{base_name}_{i + 1}.pdf")
        
        with open(output_path, "wb") as f:
            writer.write(f)
        
        # Enviem el progrés a la UI
        if callback:
            percentatge = (i + 1) / total_pages
            missatge = f"Retallant pàgina {i+1} de {total_pages}..."
            callback(percentatge, missatge)

    if callback: callback(1.0, "✅ Procés de divisió finalitzat!")