import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import ctypes

# --- CONFIGURACIÓ PER A LA ICONA A LA BARRA DE TASQUES (WINDOWS) ---
try:
    myappid = 'proxyfarming.tool.v1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

# Importem els teus mòduls
import card_downloader_and_scaler as descarregador
import pdf_maker as creador_pdf
import separador
import standalone_upscaler

class MagicApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuració de la finestra
        self.title("PROXY FARMING v1.0")
        self.geometry("900x700") 
        ctk.set_appearance_mode("dark")

        # Intentar carregar la icona
        try:
            self.iconbitmap("icona.ico")
        except:
            pass

        # --- PESTANYES PRINCIPALS ---
        self.main_tabs = ctk.CTkTabview(self, height=450)
        self.main_tabs.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        self.tab_generator = self.main_tabs.add("GENERADOR DE MAZO")
        self.tab_upscale = self.main_tabs.add("UPSCALE INDEPENDENT")

        self.setup_common_ui()
        self.setup_generator_tab()
        self.setup_upscale_tab()

    def setup_common_ui(self):
        # Zona inferior: Estat + Barra de progrés + Consola
        self.lbl_status = ctk.CTkLabel(self, text="Estat: Esperant...", text_color="gray", font=("Arial", 13, "bold"))
        self.lbl_status.pack(pady=(5, 0))
        
        self.progress_bar = ctk.CTkProgressBar(self, width=800, mode="determinate")
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)
        
        self.txt_console = ctk.CTkTextbox(self, height=200, width=850, font=("Consolas", 12))
        self.txt_console.pack(pady=(0, 10), padx=20)

    def log(self, p, m):
        """ Actualitza la interfície de manera segura des de threads """
        self.after(0, self._update_ui, p, m)

    def _update_ui(self, p, m):
        if m:
            self.txt_console.insert("end", f"{m}\n")
            self.txt_console.see("end")
            self.lbl_status.configure(text=f"Estat: {m}")
        if p is not None:
            self.progress_bar.set(float(p))

    def run_thread(self, func):
        """ Executa la lògica en segon pla per no bloquejar la UI """
        self.txt_console.delete("1.0", "end")
        self.progress_bar.set(0)
        threading.Thread(target=func, daemon=True).start()

    # ==========================================
    # PESTANYA 1: GENERADOR DE MAZO
    # ==========================================
    def setup_generator_tab(self):
        # Variables de control
        self.nom_mazo, self.ruta_pare, self.ruta_txt_existent = ctk.StringVar(), ctk.StringVar(), ctk.StringVar()
        self.ruta_imatges_custom, self.ruta_desti_pdf_custom, self.nom_pdf_custom = ctk.StringVar(), ctk.StringVar(), ctk.StringVar()
        self.sep_pdf_origen, self.sep_folder_desti = ctk.StringVar(), ctk.StringVar()
        
        self.mostrar_opcions_extra = ctk.BooleanVar(value=False)
        self.mostrar_opcions_separar = ctk.BooleanVar(value=False)
        self.executar_upscale = ctk.BooleanVar(value=False)

        self.sub_tabs = ctk.CTkTabview(self.tab_generator, height=350)
        self.sub_tabs.pack(fill="both", expand=True, padx=10, pady=5)
        
        sub_conf = self.sub_tabs.add("1. Descàrrega")
        sub_pdf = self.sub_tabs.add("2. PDF")
        sub_sep = self.sub_tabs.add("3. Separar")

        # --- SUB-TAB 1: DESCÀRREGA ---
        f_nom = ctk.CTkFrame(sub_conf, fg_color="transparent")
        f_nom.pack(pady=5)
        ctk.CTkLabel(f_nom, text="Nom del Mazo:").pack(side="left", padx=5)
        ctk.CTkEntry(f_nom, textvariable=self.nom_mazo, width=350).pack(side="left")

        f_ruta = ctk.CTkFrame(sub_conf, fg_color="transparent")
        f_ruta.pack(pady=5)
        ctk.CTkLabel(f_ruta, text="Carpeta Base:").pack(side="left", padx=5)
        ctk.CTkEntry(f_ruta, textvariable=self.ruta_pare, width=300).pack(side="left")
        ctk.CTkButton(f_ruta, text="📁", width=40, command=lambda: self.ruta_pare.set(filedialog.askdirectory())).pack(side="left", padx=5)

        self.entry_tabs = ctk.CTkTabview(sub_conf, height=140)
        self.entry_tabs.pack(fill="x", padx=15, pady=5)
        t_paste, t_file = self.entry_tabs.add("Enganxar Text"), self.entry_tabs.add("Fitxer .txt")

        self.txt_input = ctk.CTkTextbox(t_paste, height=70)
        self.txt_input.pack(fill="both", padx=5, pady=5)

        f_file_center = ctk.CTkFrame(t_file, fg_color="transparent")
        f_file_center.pack(expand=True)
        ctk.CTkEntry(f_file_center, textvariable=self.ruta_txt_existent, width=350).pack(side="left", padx=5)
        ctk.CTkButton(f_file_center, text="Cercar", command=lambda: self.ruta_txt_existent.set(filedialog.askopenfilename(filetypes=[("Text files", "*.txt")]))).pack(side="left")

        ctk.CTkSwitch(sub_conf, text="Upscale AI (x4)", variable=self.executar_upscale).pack(pady=2)
        ctk.CTkButton(sub_conf, text="INICIAR PAS 1: DESCÀRREGA", fg_color="#1f538d", font=("Arial", 12, "bold"),
                      command=lambda: self.run_thread(self.pas1_logic)).pack(pady=5)

        # --- SUB-TAB 2: GENERACIÓ DE PDF ---
        ctk.CTkSwitch(sub_pdf, text="Opcions personalitzades", variable=self.mostrar_opcions_extra, command=self.toggle_pdf_options).pack(pady=10)
        self.f_opcions_extra = ctk.CTkFrame(sub_pdf, fg_color="transparent")
        
        for lbl, var, browse in [("Nom PDF:", self.nom_pdf_custom, False), ("Origen:", self.ruta_imatges_custom, True), ("Destí:", self.ruta_desti_pdf_custom, True)]:
            f = ctk.CTkFrame(self.f_opcions_extra, fg_color="transparent")
            f.pack(pady=2)
            ctk.CTkLabel(f, text=lbl, width=100, anchor="e").pack(side="left", padx=5)
            ctk.CTkEntry(f, textvariable=var, width=300).pack(side="left")
            if browse: ctk.CTkButton(f, text="📁", width=40, command=lambda v=var: v.set(filedialog.askdirectory())).pack(side="left", padx=5)

        self.btn_generar_pdf = ctk.CTkButton(sub_pdf, text="INICIAR PAS 2: PDF", fg_color="#28a745", height=40, font=("Arial", 12, "bold"),
                                             command=lambda: self.run_thread(self.pas2_logic))
        self.btn_generar_pdf.pack(pady=20)

        # --- SUB-TAB 3: SEPARAR ---
        ctk.CTkSwitch(sub_sep, text="Opcions personalitzades", variable=self.mostrar_opcions_separar, command=self.toggle_sep_options).pack(pady=10)
        self.f_sep_extra = ctk.CTkFrame(sub_sep, fg_color="transparent")
        
        f_s1 = ctk.CTkFrame(self.f_sep_extra, fg_color="transparent")
        f_s1.pack(pady=5)
        ctk.CTkLabel(f_s1, text="PDF Origen:", width=100, anchor="e").pack(side="left", padx=5)
        ctk.CTkEntry(f_s1, textvariable=self.sep_pdf_origen, width=300).pack(side="left")
        ctk.CTkButton(f_s1, text="📄", width=40, command=lambda: self.sep_pdf_origen.set(filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")]))).pack(side="left", padx=5)

        f_s2 = ctk.CTkFrame(self.f_sep_extra, fg_color="transparent")
        f_s2.pack(pady=5)
        ctk.CTkLabel(f_s2, text="Carpeta Destí:", width=100, anchor="e").pack(side="left", padx=5)
        ctk.CTkEntry(f_s2, textvariable=self.sep_folder_desti, width=300).pack(side="left")
        ctk.CTkButton(f_s2, text="📁", width=40, command=lambda: self.sep_folder_desti.set(filedialog.askdirectory())).pack(side="left", padx=5)

        self.btn_separar_pdf = ctk.CTkButton(sub_sep, text="INICIAR PAS 3: SEPARAR PÀGINES", fg_color="#d09a1c", height=45, font=("Arial", 12, "bold"),
                                             command=lambda: self.run_thread(self.pas3_logic))
        self.btn_separar_pdf.pack(pady=20)

    def toggle_pdf_options(self):
        self.btn_generar_pdf.pack_forget()
        if self.mostrar_opcions_extra.get(): self.f_opcions_extra.pack(pady=5)
        else: self.f_opcions_extra.pack_forget()
        self.btn_generar_pdf.pack(pady=20)

    def toggle_sep_options(self):
        self.btn_separar_pdf.pack_forget()
        if self.mostrar_opcions_separar.get(): self.f_sep_extra.pack(pady=5)
        else: self.f_sep_extra.pack_forget()
        self.btn_separar_pdf.pack(pady=20)

    def obtenir_ruta_projecte(self):
        nom = self.nom_mazo.get().strip().replace(" ", "_")
        return os.path.join(self.ruta_pare.get(), nom)

    def pas1_logic(self):
        if not self.nom_mazo.get() or not self.ruta_pare.get(): return
        rp = self.obtenir_ruta_projecte()
        os.makedirs(rp, exist_ok=True)
        rtxt = os.path.join(rp, "cards.txt")
        if self.entry_tabs.get() == "Enganxar Text":
            with open(rtxt, "w", encoding="utf-8") as f: f.write(self.txt_input.get("1.0", "end-1c"))
        else: rtxt = self.ruta_txt_existent.get()
        descarregador.executar_pas1(rtxt, rp, self.executar_upscale.get(), callback=self.log)

    def pas2_logic(self):
        rp = self.obtenir_ruta_projecte()
        in_dir = self.ruta_imatges_custom.get().strip() or os.path.join(rp, "cartas_4k" if self.executar_upscale.get() else "cartas")
        out_pdf = os.path.join(self.ruta_desti_pdf_custom.get().strip() or rp, f"{self.nom_pdf_custom.get().strip() or self.nom_mazo.get()}.pdf")
        creador_pdf.generar_pdf_final(in_dir, out_pdf, callback=self.log)

    def pas3_logic(self):
        custom_pdf_in = self.sep_pdf_origen.get().strip() if self.mostrar_opcions_separar.get() else ""
        custom_folder_out = self.sep_folder_desti.get().strip() if self.mostrar_opcions_separar.get() else ""
        
        if custom_pdf_in:
            pdf_in = custom_pdf_in
        else:
            rp = self.obtenir_ruta_projecte()
            nom_pdf = f"{self.nom_pdf_custom.get().strip() or self.nom_mazo.get()}.pdf"
            pdf_in = os.path.join(self.ruta_desti_pdf_custom.get().strip() or rp, nom_pdf)

        if custom_folder_out:
            out_dir = custom_folder_out
        else:
            base_folder = os.path.dirname(pdf_in)
            out_dir = os.path.join(base_folder, "pagines_separades")

        if not os.path.exists(pdf_in):
            self.log(0, f"❌ Error: No s'ha trobat el PDF a: {pdf_in}")
            return

        os.makedirs(out_dir, exist_ok=True)
        separador.dividir_pdf(pdf_in, out_dir, callback=self.log)

    # ==========================================
    # PESTANYA 2: UPSCALE INDEPENDENT
    # ==========================================
    def setup_upscale_tab(self):
        container = ctk.CTkFrame(self.tab_upscale, fg_color="transparent")
        container.pack(expand=True)
        self.up_in, self.up_out = ctk.StringVar(), ctk.StringVar()
        ctk.CTkLabel(container, text="MILLORA D'IMATGES INDEPENDENT", font=("Arial", 16, "bold")).pack(pady=20)
        for lbl_text, var in [("Origen:", self.up_in), ("Destí:", self.up_out)]:
            f = ctk.CTkFrame(container, fg_color="transparent")
            f.pack(pady=10)
            ctk.CTkLabel(f, text=lbl_text, width=70, anchor="e").pack(side="left", padx=5)
            ctk.CTkEntry(f, textvariable=var, width=400).pack(side="left", padx=5)
            ctk.CTkButton(f, text="📁", width=45, command=lambda v=var: v.set(filedialog.askdirectory())).pack(side="left")
        ctk.CTkButton(container, text="EXECUTAR UPSCALE X4", fg_color="#e67e22", height=50, font=("Arial", 14, "bold"),
                      command=lambda: self.run_thread(self.upscale_standalone_logic)).pack(pady=30)

    def upscale_standalone_logic(self):
        """ Lògica corregida per crear la subcarpeta imatges_upscaled """
        ruta_origen = self.up_in.get().strip()
        ruta_desti_base = self.up_out.get().strip()

        if ruta_origen and ruta_desti_base:
            # Creem la subcarpeta imatges_upscaled dins del destí escollit
            final_out_dir = os.path.join(ruta_desti_base, "imatges_upscaled")
            os.makedirs(final_out_dir, exist_ok=True)
            
            standalone_upscaler.executar_upscale_folder(ruta_origen, final_out_dir, callback=self.log)

if __name__ == "__main__":
    app = MagicApp()
    app.mainloop()