import os
import sys
import subprocess

# Librerie per la conversione
from docx2pdf import convert as docx2pdf_convert
from PyPDF2 import PdfMerger
from pdf2docx import Converter as PDF2DocxConverter
from PIL import Image
import cairosvg

# PyQt5 per l'interfaccia grafica
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QComboBox, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt

# ----------------------------------
#  FUNZIONI DI CONVERSIONE
# ----------------------------------

def convert_docx_to_pdf(input_path, output_path=None):
    """docx -> pdf via docx2pdf"""
    if not output_path:
        base, _ = os.path.splitext(input_path)
        output_path = base + ".pdf"
    docx2pdf_convert(input_path, output_path)
    return output_path

def convert_pdf_to_docx(input_pdf, output_docx=None):
    """pdf -> docx via pdf2docx"""
    if not output_docx:
        base, _ = os.path.splitext(input_pdf)
        output_docx = base + ".docx"
    pdf2docx = PDF2DocxConverter(input_pdf)
    pdf2docx.convert(output_docx, start=0, end=None)
    pdf2docx.close()
    return output_docx

def convert_image(input_img, output_path):
    """
    Converte immagini raster e SVG in vari formati.
    Esempi: .png -> .jpg, .jpg -> .pdf, .svg -> .png, ecc.
    """
    ext_in = os.path.splitext(input_img)[1].lower()
    ext_out = os.path.splitext(output_path)[1].lower()

    if ext_in == ".svg":
        # SVG -> ...
        if ext_out == ".png":
            cairosvg.svg2png(url=input_img, write_to=output_path)
        elif ext_out == ".pdf":
            cairosvg.svg2pdf(url=input_img, write_to=output_path)
        elif ext_out == ".svg":
            # Se l'output è di nuovo .svg, facciamo una copia (o nulla)
            import shutil
            shutil.copy(input_img, output_path)
        elif ext_out in [".jpg", ".jpeg"]:
            # svg -> jpg? Convertendo in PNG, poi da PNG a JPG
            # per semplificare, generiamo prima un PNG temporaneo
            temp_png = output_path + "_temp.png"
            cairosvg.svg2png(url=input_img, write_to=temp_png)
            with Image.open(temp_png) as im:
                rgb_im = im.convert("RGB")  # JPG richiede RGB
                rgb_im.save(output_path, "JPEG")
            os.remove(temp_png)
        else:
            raise ValueError("Formato di output non gestito per file SVG.")
    else:
        # Raster -> ...
        with Image.open(input_img) as im:
            # Se vogliamo salvare in JPG, spesso serve convert('RGB')
            if ext_out in [".jpg", ".jpeg"]:
                im = im.convert("RGB")
                im.save(output_path, "JPEG")
            else:
                im.save(output_path)

    return output_path

def merge_pdfs(pdf_list, output_pdf):
    """Unisce più PDF in uno solo, rispettando l'ordine."""
    merger = PdfMerger()
    for pdf in pdf_list:
        merger.append(pdf)
    merger.write(output_pdf)
    merger.close()
    return output_pdf

# -------------------------
#   PDF -> .pages (macOS)
# -------------------------
def convert_pdf_to_pages(pdf_file, output_pages=None):
    """
    Converte PDF in .pages usando un doppio passaggio:
    1) PDF -> DOCX
    2) DOCX -> .pages (tramite AppleScript e Pages)
    """
    docx_temp = convert_pdf_to_docx(pdf_file)
    if not output_pages:
        base, _ = os.path.splitext(pdf_file)
        output_pages = base + ".pages"
    docx_to_pages(docx_temp, output_pages)
    return output_pages

def docx_to_pages(docx_file, pages_file=None):
    """
    Converte docx in .pages usando AppleScript.
    Richiede Apple Pages installato. Funziona solo su macOS.
    """
    if not pages_file:
        base, _ = os.path.splitext(docx_file)
        pages_file = base + ".pages"

    docx_abs = os.path.abspath(docx_file).replace('"', '\\"')
    pages_abs = os.path.abspath(pages_file).replace('"', '\\"')

    # AppleScript per dire a Pages di aprire il file docx e salvarlo come .pages
    script = f'''
    tell application "Pages"
        activate
        open "{docx_abs}"
        set theDoc to document 1
        tell theDoc to save as "com.apple.iwork.pages.sffpages" in "{pages_abs}"
        close theDoc
    end tell
    '''

    # Esegui AppleScript
    process = subprocess.run(["osascript", "-e", script],
                             capture_output=True, text=True)
    if process.returncode != 0:
        raise RuntimeError(f"Errore AppleScript: {process.stderr}")

    return pages_abs

# ---------------------------------------------------------
#   CLASSE PRINCIPALE CON QTabWidget (due tab):
#   1) Singola conversione
#   2) Merge PDF (con gestione ordine)
# ---------------------------------------------------------
class ConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Converter (PyQt5)")
        self.setMinimumSize(600, 400)

        # Stile un po' migliorato
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
                margin: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QLabel {
                font-size: 14px;
            }
            QComboBox {
                padding: 4px;
                font-size: 13px;
                margin: 4px;
            }
            QListWidget {
                background-color: #ffffff;
                margin: 4px;
            }
        """)

        # Crea i tab
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # TAB 1: Singola conversione
        self.tab_single = QWidget()
        self.tabs.addTab(self.tab_single, "Singola Conversione")
        self.setup_tab_single()

        # TAB 2: Merge PDF
        self.tab_merge = QWidget()
        self.tabs.addTab(self.tab_merge, "Merge PDF")
        self.setup_tab_merge()

    # -------------------------------------
    #  TAB 1: Singola Conversione
    # -------------------------------------
    def setup_tab_single(self):
        layout = QVBoxLayout()
        self.tab_single.setLayout(layout)

        # Label per info file
        self.label_file = QLabel("Nessun file selezionato")
        layout.addWidget(self.label_file)

        # Pulsante seleziona file
        btn_select_file = QPushButton("Seleziona File")
        btn_select_file.clicked.connect(self.select_file)
        layout.addWidget(btn_select_file)

        # Combo formati
        self.combo_format = QComboBox()
        layout.addWidget(self.combo_format)

        # Pulsante converti
        btn_convert = QPushButton("Converti")
        btn_convert.clicked.connect(self.do_conversion)
        layout.addWidget(btn_convert)

        # Label di stato
        self.label_status = QLabel("")
        layout.addWidget(self.label_status)

        # Variabili d'istanza
        self.selected_file = None

    def select_file(self):
        """Seleziona un file generico."""
        path, _ = QFileDialog.getOpenFileName(self, "Scegli un file", "", "All Files (*.*)")
        if path:
            self.selected_file = path
            base_name = os.path.basename(path)
            self.label_file.setText(f"File selezionato: {base_name}")
            self.update_possible_formats()

    def update_possible_formats(self):
        """
        In base all'estensione, aggiorna la combo di formati.
        Aggiunta di .webp e altri formati immagine.
        """
        self.combo_format.clear()
        if not self.selected_file:
            return

        ext = os.path.splitext(self.selected_file)[1].lower()
        possible_formats = []

        # docx
        if ext == ".docx":
            possible_formats = [".pdf", ".pages"]  # docx -> pdf, docx -> pages
        # pdf
        elif ext == ".pdf":
            possible_formats = [".docx", ".pages"]  # pdf -> docx, pdf -> pages
        # immagini
        elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]:
            possible_formats = [".jpg", ".png", ".pdf", ".webp"]
        # svg
        elif ext == ".svg":
            possible_formats = [".svg", ".pdf", ".png", ".jpg", ".webp"]
        else:
            possible_formats = []

        if possible_formats:
            for f in possible_formats:
                self.combo_format.addItem(f)
        else:
            self.combo_format.addItem("Formato non supportato")

    def do_conversion(self):
        """Esegue la conversione in base ai formati selezionati."""
        if not self.selected_file:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un file!")
            return

        out_ext = self.combo_format.currentText()
        if out_ext == "Formato non supportato" or out_ext == "":
            QMessageBox.warning(self, "Attenzione", "Formato non supportato o non selezionato!")
            return

        input_path = self.selected_file
        base, _ = os.path.splitext(input_path)
        output_path = base + out_ext

        try:
            in_ext = os.path.splitext(input_path)[1].lower()

            # 1) docx -> pdf
            if in_ext == ".docx" and out_ext == ".pdf":
                convert_docx_to_pdf(input_path, output_path)
                self.label_status.setText(f"Convertito in: {output_path}")

            # 2) docx -> pages
            elif in_ext == ".docx" and out_ext == ".pages":
                docx_to_pages(input_path, output_path)  # AppleScript
                self.label_status.setText(f"Convertito in: {output_path}")

            # 3) pdf -> docx
            elif in_ext == ".pdf" and out_ext == ".docx":
                convert_pdf_to_docx(input_path, output_path)
                self.label_status.setText(f"Convertito in: {output_path}")

            # 4) pdf -> pages
            elif in_ext == ".pdf" and out_ext == ".pages":
                convert_pdf_to_pages(input_path, output_path)
                self.label_status.setText(f"Convertito in: {output_path}")

            # 5) immagini / svg -> ...
            else:
                convert_image(input_path, output_path)
                self.label_status.setText(f"Convertito in: {output_path}")

        except Exception as e:
            QMessageBox.critical(self, "Errore durante la conversione", str(e))

    # -------------------------------------
    #  TAB 2: Merge PDF (con ordine)
    # -------------------------------------
    def setup_tab_merge(self):
        layout = QVBoxLayout()
        self.tab_merge.setLayout(layout)

        # Label istruzioni
        label_info = QLabel("Seleziona più PDF da unire (puoi riordinare la lista)")
        layout.addWidget(label_info)

        # ListWidget per mostrare i PDF selezionati
        self.list_pdfs = QListWidget()
        layout.addWidget(self.list_pdfs)

        # Pulsante per aggiungere PDF
        btn_add_pdf = QPushButton("Aggiungi PDF")
        btn_add_pdf.clicked.connect(self.add_pdf)
        layout.addWidget(btn_add_pdf)

        # Pulsanti per spostare su/giù l'elemento selezionato
        btn_layout = QHBoxLayout()
        btn_up = QPushButton("Su")
        btn_up.clicked.connect(self.move_item_up)
        btn_layout.addWidget(btn_up)

        btn_down = QPushButton("Giù")
        btn_down.clicked.connect(self.move_item_down)
        btn_layout.addWidget(btn_down)

        layout.addLayout(btn_layout)

        # Pulsante Merge
        btn_merge = QPushButton("Esegui Merge")
        btn_merge.clicked.connect(self.do_merge_pdfs)
        layout.addWidget(btn_merge)

        # Label di stato
        self.label_merge_status = QLabel("")
        layout.addWidget(self.label_merge_status)

    def add_pdf(self):
        """Aggiunge uno o più PDF alla lista."""
        files, _ = QFileDialog.getOpenFileNames(self, "Seleziona PDF", "", "PDF Files (*.pdf)")
        if files:
            for f in files:
                item = QListWidgetItem(f)
                self.list_pdfs.addItem(item)

    def move_item_up(self):
        """Sposta in su l'elemento selezionato."""
        current_row = self.list_pdfs.currentRow()
        if current_row > 0:
            item = self.list_pdfs.takeItem(current_row)
            self.list_pdfs.insertItem(current_row - 1, item)
            self.list_pdfs.setCurrentRow(current_row - 1)

    def move_item_down(self):
        """Sposta in giù l'elemento selezionato."""
        current_row = self.list_pdfs.currentRow()
        if current_row < self.list_pdfs.count() - 1 and current_row >= 0:
            item = self.list_pdfs.takeItem(current_row)
            self.list_pdfs.insertItem(current_row + 1, item)
            self.list_pdfs.setCurrentRow(current_row + 1)

    def do_merge_pdfs(self):
        """Unisce i PDF nell'ordine mostrato in lista."""
        n = self.list_pdfs.count()
        if n < 2:
            QMessageBox.warning(self, "Attenzione", "Aggiungi almeno 2 PDF da unire.")
            return

        pdf_list = [self.list_pdfs.item(i).text() for i in range(n)]
        # Chiediamo dove salvare il PDF unito
        output_path, _ = QFileDialog.getSaveFileName(self, "Salva PDF unito come...", "", "PDF Files (*.pdf)")
        if not output_path:
            return

        try:
            merge_pdfs(pdf_list, output_path)
            self.label_merge_status.setText(f"PDF uniti in: {output_path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore Merge PDF", str(e))

def main():
    app = QApplication(sys.argv)
    window = ConverterApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
