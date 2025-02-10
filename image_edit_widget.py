# image_edit_widget.py

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFileDialog,
    QSlider
)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QImage
from PyQt5.QtCore import Qt, QRect
from PIL import Image, ImageEnhance

class ImageEditWidget(QWidget):
    """
    Un widget che mostra un'immagine e permette:
    - Ritaglio interattivo con drag del mouse.
    - Slider luminosità (0-200%).
    - Slider opacità (0-100%).
    """
    def __init__(self):
        super().__init__()
        self.image_path = None
        self.original_pixmap = None

        self.setAcceptDrops(False)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Etichetta con l'immagine
        self.label_image = QLabel("Nessuna immagine caricata.")
        self.label_image.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_image)

        # Pulsanti
        btn_layout = QHBoxLayout()
        btn_load = QPushButton("Carica Immagine")
        btn_load.clicked.connect(self.load_image)
        btn_layout.addWidget(btn_load)

        btn_save = QPushButton("Salva Modifiche")
        btn_save.clicked.connect(self.save_edited_image)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

        # Slider luminosità
        self.slider_brightness = QSlider(Qt.Horizontal)
        self.slider_brightness.setRange(0, 200)  # 0% - 200%
        self.slider_brightness.setValue(100)     # Default 100% (no change)
        self.slider_brightness.valueChanged.connect(self.apply_adjustments)
        layout.addWidget(QLabel("Luminosità (0-200%)"))
        layout.addWidget(self.slider_brightness)

        # Slider opacità
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(0, 100)  # 0% - 100%
        self.slider_opacity.setValue(100)     # Default 100% (no change)
        self.slider_opacity.valueChanged.connect(self.apply_adjustments)
        layout.addWidget(QLabel("Opacità (0-100%)"))
        layout.addWidget(self.slider_opacity)

        # Variabili per il ritaglio
        self.start_point = None
        self.end_point = None
        self.cropping = False
        self.rect_crop = QRect()

        self.label_image.setMouseTracking(True)
        self.label_image.installEventFilter(self)

    def load_image(self):
        """Carica un'immagine da file."""
        path, _ = QFileDialog.getOpenFileName(self, "Seleziona Immagine", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        if path:
            self.image_path = path
            self.original_pixmap = QPixmap(path)
            self.label_image.setPixmap(self.original_pixmap)
            self.start_point = None
            self.end_point = None
            self.rect_crop = QRect()

    def save_edited_image(self):
        """Salva l'immagine modificata (ritaglio, luminosità, opacità) in un nuovo file."""
        if not self.image_path or self.original_pixmap is None:
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Salva Immagine", self.image_path, "Image Files (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not save_path:
            return

        # Applichiamo le modifiche su PIL
        image_pil = Image.open(self.image_path).convert("RGBA")

        # 1) Ritaglio
        if not self.rect_crop.isNull():
            # Convertiamo le coordinate della selezione in base alla dimensione reale
            crop_coords = self.get_crop_coords_for_pil()
            if crop_coords:
                left, top, right, bottom = crop_coords
                image_pil = image_pil.crop((left, top, right, bottom))

        # 2) Luminosità
        brightness_value = self.slider_brightness.value() / 100.0  # es. 1.0 = 100%
        enhancer = ImageEnhance.Brightness(image_pil)
        image_pil = enhancer.enhance(brightness_value)

        # 3) Opacità
        opacity_value = self.slider_opacity.value() / 100.0  # 1.0 = 100%
        # Convertire in RGBA e modificare alpha
        if opacity_value < 1.0:
            alpha_channel = image_pil.split()[-1]
            # alpha channel = alpha_channel * opacity_value
            # Serve iterare i pixel o usare un metodo più veloce
            alpha_data = alpha_channel.load()
            w, h = image_pil.size
            for y in range(h):
                for x in range(w):
                    alpha_data[x, y] = int(alpha_data[x, y] * opacity_value)

        # Salvataggio
        image_pil.save(save_path)

    def apply_adjustments(self):
        """Aggiorna la preview dell'immagine in base a luminosità/ opacità, per una preview veloce."""
        if not self.image_path or self.original_pixmap is None:
            return

        # Copia l'originale in PIL
        image_pil = Image.open(self.image_path).convert("RGBA")

        # Ritaglio in preview
        if not self.rect_crop.isNull():
            coords = self.get_crop_coords_for_pil()
            if coords:
                left, top, right, bottom = coords
                image_pil = image_pil.crop((left, top, right, bottom))

        # Luminosità
        brightness_value = self.slider_brightness.value() / 100.0
        enhancer = ImageEnhance.Brightness(image_pil)
        image_pil = enhancer.enhance(brightness_value)

        # Opacità
        opacity_value = self.slider_opacity.value() / 100.0
        if opacity_value < 1.0:
            alpha_channel = image_pil.split()[-1]
            alpha_data = alpha_channel.load()
            w, h = image_pil.size
            for y in range(h):
                for x in range(w):
                    alpha_data[x, y] = int(alpha_data[x, y] * opacity_value)

        # Convert PIL -> QPixmap per preview
        qimage = self.pil_to_qimage(image_pil)
        self.label_image.setPixmap(QPixmap.fromImage(qimage))

    def pil_to_qimage(self, im):
        """Converte un'immagine PIL RGBA in QImage."""
        data = im.tobytes("raw", "RGBA")
        qimage = QImage(data, im.size[0], im.size[1], QImage.Format_RGBA8888)
        return qimage

    # ----------------------
    #    MOUSE EVENTI
    # ----------------------
    def eventFilter(self, obj, event):
        """Gestione mouse per disegnare un rettangolo di ritaglio."""
        if obj is self.label_image:
            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.start_point = event.pos()
                    self.end_point = event.pos()
                    self.cropping = True
                    return True

            elif event.type() == event.MouseMove:
                if self.cropping and self.start_point is not None:
                    self.end_point = event.pos()
                    self.update_crop_rect()
                    self.label_image.update()
                return True

            elif event.type() == event.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self.cropping = False
                    self.end_point = event.pos()
                    self.update_crop_rect()
                    self.apply_adjustments()  # aggiorna la preview con ritaglio
                return True
        return super().eventFilter(obj, event)

    def update_crop_rect(self):
        if self.start_point and self.end_point:
            x1 = min(self.start_point.x(), self.end_point.x())
            y1 = min(self.start_point.y(), self.end_point.y())
            x2 = max(self.start_point.x(), self.end_point.x())
            y2 = max(self.start_point.y(), self.end_point.y())
            self.rect_crop = QRect(x1, y1, x2 - x1, y2 - y1)

    def get_crop_coords_for_pil(self):
        """Converte le coordinate del rettangolo di selezione (QRect) in coordinate dell'immagine PIL."""
        if not self.original_pixmap or self.original_pixmap.isNull():
            return None
        if self.rect_crop.isNull():
            return None

        pix_w = self.original_pixmap.width()
        pix_h = self.original_pixmap.height()

        label_w = self.label_image.width()
        label_h = self.label_image.height()

        # Factor tra dimensione reale e dimensione visibile
        scale_x = pix_w / label_w
        scale_y = pix_h / label_h

        left = int(self.rect_crop.x() * scale_x)
        top = int(self.rect_crop.y() * scale_y)
        right = int((self.rect_crop.x() + self.rect_crop.width()) * scale_x)
        bottom = int((self.rect_crop.y() + self.rect_crop.height()) * scale_y)

        return (left, top, right, bottom)
