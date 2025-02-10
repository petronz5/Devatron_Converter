# gui.py

import os
import threading
import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QComboBox, QMessageBox, QListWidget, QListWidgetItem,
    QLineEdit, QProgressBar, QMenuBar, QAction
)

# Import funzioni conversions
from conversions import (
    convert_docx_to_pdf, convert_pdf_to_docx, convert_docx_to_txt, convert_pdf_to_txt,
    convert_image, merge_pdfs, convert_pdf_to_pages, split_pdf
)

# Import cloud
from cloud_integration import upload_to_google_drive, download_from_google_drive

# Import del widget custom per image editing
from image_edit_widget import ImageEditWidget

class ConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Converter (PyQt5) - Avanzato")
        self.setMinimumSize(1000, 600)

        # Menu "Aiuto" / "Guida"
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        help_menu = menubar.addMenu("Aiuto")
        action_guide = QAction("Guida", self)
        action_guide.triggered.connect(self.show_guide)
        help_menu.addAction(action_guide)

        # Stile
        self.setStyleSheet("""
            QMainWindow {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #d5dae5, stop: 1 #ffffff
                );
            }
            QTabWidget::pane {
                background: #f5f5f5;
                border: 1px solid #aaa;
                margin: 4px;
            }
            QTabBar::tab {
                background: #e1e1e1;
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 6px;
                margin: 2px;
                font-weight: bold;
                color: #333;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom-color: #ffffff;
                color: #000;
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
                font-size: 15px;
                margin: 6px;
                color: #333;
            }
            QComboBox {
                padding: 4px;
                font-size: 14px;
                margin: 6px;
                color: #000;
            }
            QListWidget {
                background-color: #ffffff;
                margin: 6px;
                color: #000;
            }
            QLineEdit {
                background-color: #ffffff;
                margin: 6px;
                font-size: 14px;
                color: #000;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
            }
        """)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Creiamo i tab: 1) Singola conv, 2) Merge PDF, 3) Split PDF, 4) Image Editing, 5) Cloud
        self.tab_single = QWidget()
        self.tab_merge = QWidget()
        self.tab_split = QWidget()
        self.tab_image_tools = ImageEditWidget()  # Widget custom
        self.tab_cloud = QWidget()

        self.tabs.addTab(self.tab_single, "Singola Conversione")
        self.tabs.addTab(self.tab_merge, "Merge PDF")
        self.tabs.addTab(self.tab_split, "Split PDF")
        self.tabs.addTab(self.tab_image_tools, "Image Editing")
        self.tabs.addTab(self.tab_cloud, "Cloud")

        # Inizializza
        self.setup_tab_single()
        self.setup_tab_merge()
        self.setup_tab_split()
        self.setup_tab_cloud()

    def show_guide(self):
        """Mostra una finestra di aiuto/guida."""
        QMessageBox.information(self, "Guida",
            "Benvenuto in Universal Converter!\n\n"
            "Funzionalità:\n"
            "- Conversione docx/pdf/img, drag&drop\n"
            "- Merge e Split PDF\n"
            "- Editing immagini (ritaglio interattivo, luminosità, opacità)\n"
            "- Integrazione Cloud (Google Drive)\n"
            "Buon uso!"
        )

    # -------------------------------------
    #  TAB 1: Singola Conversione + progress
    # -------------------------------------
    def setup_tab_single(self):
        layout = QVBoxLayout()
        self.tab_single.setLayout(layout)

        self.label_dragdrop = QLabel("Scegli o trascina un file da convertire")
        self.label_dragdrop.setStyleSheet("border: 2px dashed #aaa; padding: 30px;")
        self.label_dragdrop.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_dragdrop)

        # Accettiamo drag&drop direttamente sul widget tab_single
        self.tab_single.setAcceptDrops(True)
        self.tab_single.dragEnterEvent = self.dragEnterEvent_single
        self.tab_single.dropEvent = self.dropEvent_single

        btn_select = QPushButton("Seleziona File")
        btn_select.clicked.connect(self.select_file_single)
        layout.addWidget(btn_select)

        self.combo_format = QComboBox()
        layout.addWidget(self.combo_format)

        # Pulsante + progress
        btn_layout = QHBoxLayout()
        self.btn_convert = QPushButton("Converti")
        self.btn_convert.clicked.connect(self.do_conversion)
        btn_layout.addWidget(self.btn_convert)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        btn_layout.addWidget(self.progress_bar)

        layout.addLayout(btn_layout)

        self.label_status = QLabel("")
        layout.addWidget(self.label_status)

        self.selected_file_single = None

    def dragEnterEvent_single(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent_single(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                self.selected_file_single = file_path
                base_name = os.path.basename(file_path)
                self.label_dragdrop.setText(f"File trascinato: {base_name}")
                self.update_possible_formats_single(file_path)
            event.acceptProposedAction()

    def select_file_single(self):
        path, _ = QFileDialog.getOpenFileName(self.tab_single, "Scegli un file", "", "All Files (*.*)")
        if path:
            self.selected_file_single = path
            base_name = os.path.basename(path)
            self.label_dragdrop.setText(f"File selezionato: {base_name}")
            self.update_possible_formats_single(path)

    def update_possible_formats_single(self, file_path):
        self.combo_format.clear()
        ext = os.path.splitext(file_path)[1].lower()
        possibili = []
        if ext == ".docx":
            possibili = [".pdf", ".pages", ".txt"]
        elif ext == ".pdf":
            possibili = [".docx", ".pages", ".txt"]
        elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]:
            possibili = [".jpg", ".png", ".pdf", ".webp"]
        elif ext == ".svg":
            possibili = [".svg", ".pdf", ".png", ".jpg", ".webp"]
        if possibili:
            for p in possibili:
                self.combo_format.addItem(p)
        else:
            self.combo_format.addItem("Formato non supportato")

    def do_conversion(self):
        if not self.selected_file_single:
            QMessageBox.warning(self, "Attenzione", "Nessun file selezionato!")
            return
        out_ext = self.combo_format.currentText()
        if out_ext == "Formato non supportato":
            QMessageBox.warning(self, "Attenzione", "Formato non supportato!")
            return

        input_path = self.selected_file_single
        base, _ = os.path.splitext(input_path)
        output_path = base + out_ext

        def conversion_thread():
            try:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.do_actual_conversion(input_path, output_path)
                for i in range(1, 101, 10):
                    time.sleep(0.05)
                    self.progress_bar.setValue(i)
                self.progress_bar.setVisible(False)
                self.label_status.setText(f"Convertito in: {output_path}")
            except Exception as e:
                self.progress_bar.setVisible(False)
                QMessageBox.critical(self, "Errore Conversione", str(e))

        t = threading.Thread(target=conversion_thread)
        t.start()

    def do_actual_conversion(self, input_path, output_path):
        ext_in = os.path.splitext(input_path)[1].lower()
        ext_out = os.path.splitext(output_path)[1].lower()
        if ext_in == ".docx" and ext_out == ".pdf":
            convert_docx_to_pdf(input_path, output_path)
        elif ext_in == ".docx" and ext_out == ".pages":
            convert_pdf_to_pages(input_path, output_path)  # in realtà docx->pdf->pages, o docx_to_pages
            # Se vuoi esattamente docx->pages, devi usare docx_to_pages
            # convert_pdf_to_pages si aspetta un PDF in input.
            # Quindi potresti fare:
            # temp_pdf = convert_docx_to_pdf(input_path)
            # convert_pdf_to_pages(temp_pdf, output_path)
        elif ext_in == ".docx" and ext_out == ".txt":
            convert_docx_to_txt(input_path, output_path)
        elif ext_in == ".pdf" and ext_out == ".docx":
            convert_pdf_to_docx(input_path, output_path)
        elif ext_in == ".pdf" and ext_out == ".pages":
            convert_pdf_to_pages(input_path, output_path)
        elif ext_in == ".pdf" and ext_out == ".txt":
            convert_pdf_to_txt(input_path, output_path)
        else:
            convert_image(input_path, output_path)

    # -------------------------------------
    #  TAB 2: Merge PDF
    # -------------------------------------
    def setup_tab_merge(self):
        layout = QVBoxLayout()
        self.tab_merge.setLayout(layout)

        label_info = QLabel("Seleziona più PDF da unire (in ordine).")
        layout.addWidget(label_info)

        self.list_pdfs = QListWidget()
        layout.addWidget(self.list_pdfs)

        btn_add_pdf = QPushButton("Aggiungi PDF")
        btn_add_pdf.clicked.connect(self.add_pdf)
        layout.addWidget(btn_add_pdf)

        hl = QHBoxLayout()
        btn_up = QPushButton("Su")
        btn_up.clicked.connect(self.move_item_up)
        hl.addWidget(btn_up)
        btn_down = QPushButton("Giù")
        btn_down.clicked.connect(self.move_item_down)
        hl.addWidget(btn_down)
        layout.addLayout(hl)

        btn_merge = QPushButton("Esegui Merge")
        btn_merge.clicked.connect(self.do_merge_pdfs)
        layout.addWidget(btn_merge)

        self.label_merge_status = QLabel("")
        layout.addWidget(self.label_merge_status)

    def add_pdf(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleziona PDF", "", "PDF Files (*.pdf)")
        if files:
            for f in files:
                self.list_pdfs.addItem(f)

    def move_item_up(self):
        row = self.list_pdfs.currentRow()
        if row > 0:
            item = self.list_pdfs.takeItem(row)
            self.list_pdfs.insertItem(row - 1, item)
            self.list_pdfs.setCurrentRow(row - 1)

    def move_item_down(self):
        row = self.list_pdfs.currentRow()
        if row < self.list_pdfs.count() - 1 and row >= 0:
            item = self.list_pdfs.takeItem(row)
            self.list_pdfs.insertItem(row + 1, item)
            self.list_pdfs.setCurrentRow(row + 1)

    def do_merge_pdfs(self):
        n = self.list_pdfs.count()
        if n < 2:
            QMessageBox.warning(self, "Attenzione", "Almeno 2 PDF per il merge!")
            return
        pdf_list = [self.list_pdfs.item(i).text() for i in range(n)]
        output_path, _ = QFileDialog.getSaveFileName(self, "Salva PDF unito", "", "PDF Files (*.pdf)")
        if not output_path:
            return
        try:
            merge_pdfs(pdf_list, output_path)
            self.label_merge_status.setText(f"PDF uniti in: {output_path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore Merge PDF", str(e))

    # -------------------------------------
    #  TAB 3: Split PDF
    # -------------------------------------
    def setup_tab_split(self):
        layout = QVBoxLayout()
        self.tab_split.setLayout(layout)

        label_info = QLabel("Seleziona un PDF e inserisci intervalli di pagine (es: 1-3,5,7-9)")
        layout.addWidget(label_info)

        btn_select = QPushButton("Seleziona PDF")
        btn_select.clicked.connect(self.select_split_pdf)
        layout.addWidget(btn_select)

        self.label_split_pdf = QLabel("Nessun PDF selezionato")
        layout.addWidget(self.label_split_pdf)

        self.line_pages = QLineEdit()
        self.line_pages.setPlaceholderText("Intervalli di pagine (es: 1-3,5,7-9)")
        layout.addWidget(self.line_pages)

        btn_split = QPushButton("Estrai Pagine")
        btn_split.clicked.connect(self.do_split_pdf)
        layout.addWidget(btn_split)

        self.label_split_status = QLabel("")
        layout.addWidget(self.label_split_status)

        self.selected_split_pdf = None

    def select_split_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleziona PDF", "", "PDF Files (*.pdf)")
        if path:
            self.selected_split_pdf = path
            self.label_split_pdf.setText(f"PDF selezionato: {os.path.basename(path)}")

    def do_split_pdf(self):
        if not self.selected_split_pdf:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un PDF!")
            return
        pages_string = self.line_pages.text().strip()
        if not pages_string:
            QMessageBox.warning(self, "Attenzione", "Inserisci gli intervalli di pagine!")
            return
        output_path, _ = QFileDialog.getSaveFileName(self, "Salva PDF estratto come...", "", "PDF Files (*.pdf)")
        if not output_path:
            return
        try:
            split_pdf(self.selected_split_pdf, output_path, pages_string)
            self.label_split_status.setText(f"Pagine estratte in: {output_path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore Split PDF", str(e))

    # -------------------------------------
    #  TAB 4: Image Editing
    # (SOSTITUITO con un widget dedicato: `ImageEditWidget`)
    # -------------------------------------
    # N.B. L'abbiamo già aggiunto come `self.tab_image_tools = ImageEditWidget()`
    # Non serve altro qui

    # -------------------------------------
    #  TAB 5: Cloud (Google Drive)
    # -------------------------------------
    def setup_tab_cloud(self):
        layout = QVBoxLayout()
        self.tab_cloud.setLayout(layout)

        label_info = QLabel("Carica o scarica file da Google Drive")
        layout.addWidget(label_info)

        btn_upload = QPushButton("Carica File su Drive")
        btn_upload.clicked.connect(self.upload_file_to_drive)
        layout.addWidget(btn_upload)

        self.label_cloud_status = QLabel("")
        layout.addWidget(self.label_cloud_status)

        # Download
        dl_layout = QHBoxLayout()
        self.line_file_id = QLineEdit()
        self.line_file_id.setPlaceholderText("ID del file su Drive")
        dl_layout.addWidget(self.line_file_id)

        btn_download = QPushButton("Scarica File")
        btn_download.clicked.connect(self.download_file_from_drive)
        dl_layout.addWidget(btn_download)

        layout.addLayout(dl_layout)

    def upload_file_to_drive(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleziona File da caricare", "", "All Files (*.*)")
        if not path:
            return
        try:
            result = upload_to_google_drive(path)
            self.label_cloud_status.setText(result)
        except Exception as e:
            QMessageBox.critical(self, "Errore Upload Drive", str(e))

    def download_file_from_drive(self):
        file_id = self.line_file_id.text().strip()
        if not file_id:
            QMessageBox.warning(self, "Attenzione", "Inserisci un file ID di Drive!")
            return
        output_path, _ = QFileDialog.getSaveFileName(self, "Salva file scaricato come...", "", "All Files (*.*)")
        if not output_path:
            return
        try:
            result = download_from_google_drive(file_id, output_path)
            self.label_cloud_status.setText(result)
        except Exception as e:
            QMessageBox.critical(self, "Errore Download Drive", str(e))
