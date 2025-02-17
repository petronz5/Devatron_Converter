import os
import json
import threading
import time

from PyQt5.QtCore import QSettings, QDateTime, Qt, QPropertyAnimation, QEasingCurve, QRectF
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QFileDialog, QComboBox, QMessageBox, QListWidget, QLineEdit, QProgressBar,
    QStackedWidget, QDialog, QToolBar, QTabWidget, QSpinBox, QFormLayout, QCheckBox,
    QSlider, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
)

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    InstalledAppFlow = None

from conversions import (
    convert_docx_to_pdf, convert_pdf_to_docx, convert_docx_to_txt, convert_pdf_to_txt,
    convert_image, merge_pdfs, convert_pdf_to_pages, split_pdf
)
from cloud_integration import upload_to_drive

# -------------------------------------------------------------------
# FUNZIONI di login persistente (definite a livello globale)
# -------------------------------------------------------------------
def save_login(username):
    settings = QSettings("MyCompany", "ConverterApp")
    settings.setValue("username", username)
    settings.setValue("login_date", QDateTime.currentDateTime().toSecsSinceEpoch())

def check_login():
    settings = QSettings("MyCompany", "ConverterApp")
    username = settings.value("username", "")
    login_date = settings.value("login_date", 0, type=int)
    if username and login_date:
        current = QDateTime.currentDateTime().toSecsSinceEpoch()
        if current - login_date < 30 * 24 * 3600:
            return username
    return None

def clear_login():
    settings = QSettings("MyCompany", "ConverterApp")
    settings.clear()

# =========================================================
#   LanguageManager: Gestisce le traduzioni (it, en, es, fr)
# =========================================================
class LanguageManager:
    def __init__(self):
        self.translations = {
            "it": {
                "LOGIN_TITLE": "ACCEDI",
                "LOGIN_USERNAME": "Username:",
                "LOGIN_PASSWORD": "Password:",
                "LOGIN_BUTTON": "Login",
                "REGISTER_BUTTON": "Registrati",
                "REGISTER_TITLE": "Registrazione",
                "REGISTER_USERNAME": "Username:",
                "REGISTER_PASSWORD": "Password:",
                "REGISTER_CONFIRM": "Conferma Password:",
                "OLD_PASSWORD": "Vecchia Password:",
                "CANCEL_BUTTON": "Annulla",
                "SINGLE_INFO": "Trascina qui un file oppure clicca 'Seleziona File'",
                "SELECT_FILE": "Seleziona File",
                "ADVANCED_OPTIONS": "Opzioni Avanzate",
                "CONVERT_BUTTON": "Converti",
                "UPLOAD_DRIVE": "Carica su Drive",
                "MERGE_INFO": "Trascina qui i file PDF da unire oppure usa 'Aggiungi PDF'",
                "ADD_PDF": "Aggiungi PDF",
                "MOVE_UP": "Su",
                "MOVE_DOWN": "Giù",
                "MERGE_BUTTON": "Unisci PDF",
                "SPLIT_INFO": "Trascina qui un PDF oppure usa 'Seleziona PDF'",
                "SELECT_PDF": "Seleziona PDF",
                "EXTRACT_PAGES": "Estrai Pagine",
                "SETTINGS_TITLE": "Impostazioni",
                "LANGUAGE_LABEL": "Seleziona Lingua:",
                "THEME_SWITCH": "Cambio Tema",
                "USER_INFO": "Nome: {username}\nPassword: {password}",
                "SWITCH_TO_DARK": "Passa a Tema Scuro",
                "SWITCH_TO_LIGHT": "Passa a Tema Chiaro",
                "GOOGLE_LOGIN": "Login con Google",
                "OPTIONS": "Opzioni",
                "OPT_TAB_LANGUAGE": "Lingua",
                "OPT_TAB_THEME": "Tema",
                "OPT_TAB_USER": "Utente",
                "OPT_LANGUAGE": "Cambia lingua",
                "OPT_THEME": "Seleziona tema",
                "OPT_THEME_CHOICE": "Tema:",
                "OPT_USER_CHANGE": "Cambia password",
                "NEW_PASSWORD": "Nuova Password:",
                "CONFIRM_PASSWORD": "Conferma Password:",
                "UPDATE_PASSWORD": "Aggiorna Password",
                "PASSWORD_UPDATED": "Password aggiornata con successo!",
                "LOGOUT": "Esci",
                "IMAGE_EDITOR": "Modifica Immagine",
                "LOAD_IMAGE": "Carica Immagine",
                "SCALE_IMAGE": "Scala Immagine",
                "CROP_IMAGE": "Ritaglia",
                "APPLY_EFFECT": "Applica Effetto (B/N)",
                "USER_ICON": "Utente: "
            },
            "en": {
                "LOGIN_TITLE": "LOGIN",
                "LOGIN_USERNAME": "Username:",
                "LOGIN_PASSWORD": "Password:",
                "LOGIN_BUTTON": "Login",
                "REGISTER_BUTTON": "Register",
                "REGISTER_TITLE": "Registration",
                "REGISTER_USERNAME": "Username:",
                "REGISTER_PASSWORD": "Password:",
                "REGISTER_CONFIRM": "Confirm Password:",
                "OLD_PASSWORD": "Old Password:",
                "CANCEL_BUTTON": "Cancel",
                "SINGLE_INFO": "Drag a file here or click 'Select File'",
                "SELECT_FILE": "Select File",
                "ADVANCED_OPTIONS": "Advanced Options",
                "CONVERT_BUTTON": "Convert",
                "UPLOAD_DRIVE": "Upload to Drive",
                "MERGE_INFO": "Drag PDF files to merge or click 'Add PDF'",
                "ADD_PDF": "Add PDF",
                "MOVE_UP": "Up",
                "MOVE_DOWN": "Down",
                "MERGE_BUTTON": "Merge PDF",
                "SPLIT_INFO": "Drag a PDF here or click 'Select PDF'",
                "SELECT_PDF": "Select PDF",
                "EXTRACT_PAGES": "Extract Pages",
                "SETTINGS_TITLE": "Settings",
                "LANGUAGE_LABEL": "Select Language:",
                "THEME_SWITCH": "Theme Switch",
                "USER_INFO": "Name: {username}\nPassword: {password}",
                "SWITCH_TO_DARK": "Switch to Dark Theme",
                "SWITCH_TO_LIGHT": "Switch to Light Theme",
                "GOOGLE_LOGIN": "Login with Google",
                "OPTIONS": "Options",
                "OPT_TAB_LANGUAGE": "Language",
                "OPT_TAB_THEME": "Theme",
                "OPT_TAB_USER": "User",
                "OPT_LANGUAGE": "Change language",
                "OPT_THEME": "Select theme",
                "OPT_THEME_CHOICE": "Theme:",
                "OPT_USER_CHANGE": "Change password",
                "NEW_PASSWORD": "New Password:",
                "CONFIRM_PASSWORD": "Confirm Password:",
                "UPDATE_PASSWORD": "Update Password",
                "PASSWORD_UPDATED": "Password updated successfully!",
                "LOGOUT": "Logout",
                "IMAGE_EDITOR": "Image Editor",
                "LOAD_IMAGE": "Load Image",
                "SCALE_IMAGE": "Scale Image",
                "CROP_IMAGE": "Crop",
                "APPLY_EFFECT": "Apply Effect (B/W)",
                "USER_ICON": "User: "
            },
            "es": {
                "LOGIN_TITLE": "INICIAR SESIÓN",
                "LOGIN_USERNAME": "Usuario:",
                "LOGIN_PASSWORD": "Contraseña:",
                "LOGIN_BUTTON": "Entrar",
                "REGISTER_BUTTON": "Registrarse",
                "REGISTER_TITLE": "Registro",
                "REGISTER_USERNAME": "Usuario:",
                "REGISTER_PASSWORD": "Contraseña:",
                "REGISTER_CONFIRM": "Confirmar Contraseña:",
                "OLD_PASSWORD": "Contraseña Anterior:",
                "CANCEL_BUTTON": "Cancelar",
                "SINGLE_INFO": "Arrastra un archivo o haz clic en 'Seleccionar Archivo'",
                "SELECT_FILE": "Seleccionar Archivo",
                "ADVANCED_OPTIONS": "Opciones Avanzadas",
                "CONVERT_BUTTON": "Convertir",
                "UPLOAD_DRIVE": "Subir a Drive",
                "MERGE_INFO": "Arrastra archivos PDF o haz clic en 'Agregar PDF'",
                "ADD_PDF": "Agregar PDF",
                "MOVE_UP": "Subir",
                "MOVE_DOWN": "Bajar",
                "MERGE_BUTTON": "Unir PDF",
                "SPLIT_INFO": "Arrastra un PDF o haz clic en 'Seleccionar PDF'",
                "SELECT_PDF": "Seleccionar PDF",
                "EXTRACT_PAGES": "Extraer Páginas",
                "SETTINGS_TITLE": "Configuración",
                "LANGUAGE_LABEL": "Seleccionar Idioma:",
                "THEME_SWITCH": "Cambiar Tema",
                "USER_INFO": "Nombre: {username}\nContraseña: {password}",
                "SWITCH_TO_DARK": "Cambiar a Tema Oscuro",
                "SWITCH_TO_LIGHT": "Cambiar a Tema Claro",
                "GOOGLE_LOGIN": "Iniciar con Google",
                "OPTIONS": "Opciones",
                "OPT_TAB_LANGUAGE": "Idioma",
                "OPT_TAB_THEME": "Tema",
                "OPT_TAB_USER": "Usuario",
                "OPT_LANGUAGE": "Cambiar idioma",
                "OPT_THEME": "Seleccionar tema",
                "OPT_THEME_CHOICE": "Tema:",
                "OPT_USER_CHANGE": "Cambiar contraseña",
                "NEW_PASSWORD": "Nueva Contraseña:",
                "CONFIRM_PASSWORD": "Confirmar Contraseña:",
                "UPDATE_PASSWORD": "Actualizar Contraseña",
                "PASSWORD_UPDATED": "¡Contraseña actualizada con éxito!",
                "LOGOUT": "Salir",
                "IMAGE_EDITOR": "Editar Imagen",
                "LOAD_IMAGE": "Cargar Imagen",
                "SCALE_IMAGE": "Escalar Imagen",
                "CROP_IMAGE": "Recortar",
                "APPLY_EFFECT": "Aplicar Efecto (B/N)",
                "USER_ICON": "Usuario: "
            },
            "fr": {
                "LOGIN_TITLE": "CONNEXION",
                "LOGIN_USERNAME": "Nom d'utilisateur:",
                "LOGIN_PASSWORD": "Mot de passe:",
                "LOGIN_BUTTON": "Se Connecter",
                "REGISTER_BUTTON": "S'inscrire",
                "REGISTER_TITLE": "Inscription",
                "REGISTER_USERNAME": "Nom d'utilisateur:",
                "REGISTER_PASSWORD": "Mot de passe:",
                "REGISTER_CONFIRM": "Confirmer le mot de passe:",
                "OLD_PASSWORD": "Ancien mot de passe:",
                "CANCEL_BUTTON": "Annuler",
                "SINGLE_INFO": "Glissez un fichier ici ou cliquez sur 'Sélectionner un fichier'",
                "SELECT_FILE": "Sélectionner un fichier",
                "ADVANCED_OPTIONS": "Options Avancées",
                "CONVERT_BUTTON": "Convertir",
                "UPLOAD_DRIVE": "Téléverser sur Drive",
                "MERGE_INFO": "Glissez des PDF ou cliquez sur 'Ajouter PDF'",
                "ADD_PDF": "Ajouter PDF",
                "MOVE_UP": "Monter",
                "MOVE_DOWN": "Descendre",
                "MERGE_BUTTON": "Fusionner PDF",
                "SPLIT_INFO": "Glissez un PDF ou cliquez sur 'Sélectionner PDF'",
                "SELECT_PDF": "Sélectionner PDF",
                "EXTRACT_PAGES": "Extraire Pages",
                "SETTINGS_TITLE": "Paramètres",
                "LANGUAGE_LABEL": "Sélectionner la Langue:",
                "THEME_SWITCH": "Changer de Thème",
                "USER_INFO": "Nom: {username}\nMot de passe: {password}",
                "SWITCH_TO_DARK": "Passer au Thème Sombre",
                "SWITCH_TO_LIGHT": "Passer au Thème Clair",
                "GOOGLE_LOGIN": "Se connecter avec Google",
                "OPTIONS": "Options",
                "OPT_TAB_LANGUAGE": "Langue",
                "OPT_TAB_THEME": "Thème",
                "OPT_TAB_USER": "Utilisateur",
                "OPT_LANGUAGE": "Changer la langue",
                "OPT_THEME": "Sélectionner le thème",
                "OPT_THEME_CHOICE": "Thème:",
                "OPT_USER_CHANGE": "Changer le mot de passe",
                "NEW_PASSWORD": "Nouveau Mot de passe:",
                "CONFIRM_PASSWORD": "Confirmer le Mot de passe:",
                "UPDATE_PASSWORD": "Mettre à jour le Mot de passe",
                "PASSWORD_UPDATED": "Mot de passe mis à jour avec succès!",
                "LOGOUT": "Se Déconnecter",
                "IMAGE_EDITOR": "Éditer l'Image",
                "LOAD_IMAGE": "Charger l'Image",
                "SCALE_IMAGE": "Redimensionner l'Image",
                "CROP_IMAGE": "Recadrer",
                "APPLY_EFFECT": "Appliquer l'Effet (N/B)",
                "USER_ICON": "Utilisateur: "
            }
        }

    def get_text(self, lang, key, **kwargs):
        if lang not in self.translations:
            lang = "it"
        text = self.translations[lang].get(key, key)
        if kwargs:
            text = text.format(**kwargs)
        return text
# =========================================================
#   OptionsDialog: classe definita nello stesso file
# =========================================================
class OptionsDialog(QDialog):
    def __init__(self, current_lang, current_theme, username):
        super().__init__()
        self.setWindowTitle("Opzioni")
        self.setFixedSize(400, 320)
        self.language = current_lang
        self.theme = current_theme
        self.username = username
        self.lm = LanguageManager()
        
        tab_widget = QTabWidget()
        layout = QVBoxLayout()
        layout.addWidget(tab_widget)
        self.setLayout(layout)
        
        # Scheda Lingua
        lang_tab = QWidget()
        lang_layout = QVBoxLayout()
        lang_tab.setLayout(lang_layout)
        lang_label = QLabel(self.lm.get_text(self.language, "OPT_LANGUAGE"))
        lang_layout.addWidget(lang_label)
        self.combo_language = QComboBox()
        self.combo_language.addItem("Italiano (it)", "it")
        self.combo_language.addItem("English (en)", "en")
        self.combo_language.addItem("Español (es)", "es")
        self.combo_language.addItem("Français (fr)", "fr")
        index = self.combo_language.findData(self.language)
        if index >= 0:
            self.combo_language.setCurrentIndex(index)
        lang_layout.addWidget(self.combo_language)
        tab_widget.addTab(lang_tab, self.lm.get_text(self.language, "OPT_TAB_LANGUAGE"))
        
        # Scheda Tema
        theme_tab = QWidget()
        theme_layout = QVBoxLayout()
        theme_tab.setLayout(theme_layout)
        theme_label = QLabel(self.lm.get_text(self.language, "OPT_THEME"))
        theme_layout.addWidget(theme_label)
        self.combo_theme = QComboBox()
        self.combo_theme.addItem("Chiaro", "light")
        self.combo_theme.addItem("Scuro", "dark")
        idx = self.combo_theme.findData(self.theme)
        if idx >= 0:
            self.combo_theme.setCurrentIndex(idx)
        theme_layout.addWidget(self.combo_theme)
        tab_widget.addTab(theme_tab, self.lm.get_text(self.language, "OPT_TAB_THEME"))
        
        # Scheda Utente (cambio password con vecchia password e occhiello)
        user_tab = QWidget()
        user_layout = QFormLayout()
        user_tab.setLayout(user_layout)
        self.label_current_user = QLabel(self.username)
        user_layout.addRow(self.lm.get_text(self.language, "USER_ICON"), self.label_current_user)
        
        # Campo vecchia password
        self.edit_old_password = QLineEdit()
        self.edit_old_password.setEchoMode(QLineEdit.Password)
        user_layout.addRow(self.lm.get_text(self.language, "OLD_PASSWORD"), self.edit_old_password)
        
        # Campo nuova password + occhiello
        self.edit_new_password = QLineEdit()
        self.edit_new_password.setEchoMode(QLineEdit.Password)
        self.btn_eye_new = QPushButton("👁")
        self.btn_eye_new.setCheckable(True)
        self.btn_eye_new.toggled.connect(self.toggle_new_password)
        hbox_new = QHBoxLayout()
        hbox_new.addWidget(self.edit_new_password)
        hbox_new.addWidget(self.btn_eye_new)
        user_layout.addRow(self.lm.get_text(self.language, "NEW_PASSWORD"), hbox_new)
        
        # Campo conferma password + occhiello
        self.edit_confirm_password = QLineEdit()
        self.edit_confirm_password.setEchoMode(QLineEdit.Password)
        self.btn_eye_confirm = QPushButton("👁")
        self.btn_eye_confirm.setCheckable(True)
        self.btn_eye_confirm.toggled.connect(self.toggle_confirm_password)
        hbox_conf = QHBoxLayout()
        hbox_conf.addWidget(self.edit_confirm_password)
        hbox_conf.addWidget(self.btn_eye_confirm)
        user_layout.addRow(self.lm.get_text(self.language, "CONFIRM_PASSWORD"), hbox_conf)
        
        self.btn_update_password = QPushButton(self.lm.get_text(self.language, "UPDATE_PASSWORD"))
        self.btn_update_password.clicked.connect(self.update_password)
        user_layout.addRow(self.btn_update_password)
        tab_widget.addTab(user_tab, self.lm.get_text(self.language, "OPT_TAB_USER"))
        
        # Pulsanti OK/Cancel
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton(self.lm.get_text(self.language, "CANCEL_BUTTON"))
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def toggle_new_password(self, checked):
        if checked:
            self.edit_new_password.setEchoMode(QLineEdit.Normal)
        else:
            self.edit_new_password.setEchoMode(QLineEdit.Password)
    
    def toggle_confirm_password(self, checked):
        if checked:
            self.edit_confirm_password.setEchoMode(QLineEdit.Normal)
        else:
            self.edit_confirm_password.setEchoMode(QLineEdit.Password)
    
    def update_password(self):
        old_pass = self.edit_old_password.text()
        new_pass = self.edit_new_password.text()
        conf_pass = self.edit_confirm_password.text()
        if not old_pass or not new_pass or not conf_pass:
            QMessageBox.warning(self, "Errore", "Inserisci tutte le password richieste.")
            return
        if new_pass != conf_pass:
            QMessageBox.warning(self, "Errore", "Le nuove password non coincidono.")
            return
        try:
            with open("users.json", "r") as f:
                users_data = json.load(f)
            if self.username not in users_data:
                QMessageBox.warning(self, "Errore", "Utente non trovato.")
                return
            if users_data[self.username] != old_pass:
                QMessageBox.warning(self, "Errore", "La vecchia password non è corretta.")
                return
            users_data[self.username] = new_pass
            with open("users.json", "w") as f:
                json.dump(users_data, f, indent=2)
            QMessageBox.information(self, "OK", self.lm.get_text(self.language, "PASSWORD_UPDATED"))
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante l'aggiornamento della password:\n{str(e)}")
    
    def update_language(self, lang, lm):
        self.language = lang
        self.setWindowTitle(lm.get_text(lang, "OPTIONS", default="Opzioni"))

# =========================================================
#   ImageEditorWidget: Per modificare immagini in tempo reale
# =========================================================
class ImageEditorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_pixmap = None
        self.crop_rect_item = None
        self.is_selecting = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label_title = QLabel("Modifica Immagine")
        layout.addWidget(self.label_title)

        # Riga dei pulsanti: Carica, Effetto B/N, Ritaglia
        hbox_btn = QHBoxLayout()
        self.btn_load = QPushButton("Carica Immagine")
        self.btn_load.clicked.connect(self.load_image)
        hbox_btn.addWidget(self.btn_load)

        self.btn_apply_effect = QPushButton("B/N")
        self.btn_apply_effect.clicked.connect(self.apply_bw_effect)
        hbox_btn.addWidget(self.btn_apply_effect)

        self.btn_crop = QPushButton("Ritaglia")
        self.btn_crop.clicked.connect(self.do_crop)
        hbox_btn.addWidget(self.btn_crop)
        layout.addLayout(hbox_btn)

        # Slider per scaling
        self.slider_scale = QSlider(Qt.Horizontal)
        self.slider_scale.setRange(1, 300)
        self.slider_scale.setValue(100)
        self.slider_scale.valueChanged.connect(self.scale_image)
        layout.addWidget(self.slider_scale)

        # Campo di input per dimensioni manuali (nuova larghezza)
        dim_layout = QHBoxLayout()
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("Nuova larghezza")
        dim_layout.addWidget(self.width_input)
        self.apply_size_btn = QPushButton("Applica dimensioni")
        self.apply_size_btn.clicked.connect(self.apply_new_dimensions)
        dim_layout.addWidget(self.apply_size_btn)
        layout.addLayout(dim_layout)

        # Vista grafica per mostrare l'immagine
        self.graphics_view = QGraphicsView()
        layout.addWidget(self.graphics_view)
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        self.graphics_view.setMouseTracking(True)
        self.graphics_view.viewport().installEventFilter(self)

        # Pulsante per salvare l'immagine modificata
        self.btn_save = QPushButton("Salva Immagine")
        self.btn_save.clicked.connect(self.save_image)
        layout.addWidget(self.btn_save)

    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Carica Immagine", "", 
                                              "Immagini (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            pm = QPixmap(path)
            if pm.isNull():
                QMessageBox.warning(self, "Errore", "Immagine non valida.")
                return
            self.current_pixmap = pm
            self.show_pixmap(pm)

    def show_pixmap(self, pm):
        self.scene.clear()
        # Resetta lo slider al 100%
        self.slider_scale.setValue(100)
        self.pixmap_item = QGraphicsPixmapItem(pm)
        self.scene.addItem(self.pixmap_item)
        self.scene.setSceneRect(self.pixmap_item.boundingRect())
        self.crop_rect_item = None

    def scale_image(self):
        if self.current_pixmap:
            scale_val = self.slider_scale.value()
            new_w = int(self.current_pixmap.width() * scale_val / 100)
            pm_scaled = self.current_pixmap.scaledToWidth(new_w, Qt.SmoothTransformation)
            self.show_pixmap(pm_scaled)

    def apply_new_dimensions(self, instance):
        if not self.current_pixmap:
            QMessageBox.warning(self, "Errore", "Nessuna immagine caricata!")
            return
        try:
            new_width = int(self.width_input.text())
        except ValueError:
            QMessageBox.warning(self, "Errore", "Inserisci un valore numerico valido per la larghezza!")
            return
        # Calcola l'altezza in modo da mantenere il rapporto d'aspetto
        aspect_ratio = self.current_pixmap.height() / self.current_pixmap.width()
        new_height = int(new_width * aspect_ratio)
        scaled_pixmap = self.current_pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.show_pixmap(scaled_pixmap)

    def save_image(self):
        if not self.current_pixmap:
            QMessageBox.warning(self, "Errore", "Nessuna immagine da salvare!")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salva Immagine", "", 
                                              "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)")
        if path:
            if not self.current_pixmap.save(path):
                QMessageBox.critical(self, "Errore", "Impossibile salvare l'immagine.")
            else:
                QMessageBox.information(self, "Salvataggio", "Immagine salvata correttamente!")

    def apply_bw_effect(self):
        if not self.current_pixmap:
            return
        image = self.current_pixmap.toImage()
        for y in range(image.height()):
            for x in range(image.width()):
                c = image.pixelColor(x, y)
                gray = int(0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue())
                image.setPixelColor(x, y, QColor(gray, gray, gray))
        self.current_pixmap = QPixmap.fromImage(image)
        self.show_pixmap(self.current_pixmap)

    def do_crop(self):
        if not self.current_pixmap or not self.crop_rect_item:
            return
        rectF = self.crop_rect_item.mapRectToScene(self.crop_rect_item.rect())
        img_x = max(int(rectF.left()), 0)
        img_y = max(int(rectF.top()), 0)
        img_w = int(rectF.width())
        img_h = int(rectF.height())
        cropped = self.current_pixmap.copy(img_x, img_y, img_w, img_h)
        self.current_pixmap = cropped
        self.show_pixmap(cropped)

    def eventFilter(self, obj, event):
        if obj == self.graphics_view.viewport():
            if event.type() == event.MouseButtonPress:
                self.is_selecting = True
                self.start_pos = event.pos()
                if self.crop_rect_item:
                    self.scene.removeItem(self.crop_rect_item)
                self.crop_rect_item = QGraphicsRectItem(0, 0, 0, 0)
                self.crop_rect_item.setPen(QColor(255, 0, 0))
                self.scene.addItem(self.crop_rect_item)
                return True
            elif event.type() == event.MouseMove and self.is_selecting:
                end_pos = event.pos()
                rect = self.normalize_rect(self.start_pos, end_pos)
                self.crop_rect_item.setRect(rect)
                return True
            elif event.type() == event.MouseButtonRelease:
                self.is_selecting = False
                return True
        return super().eventFilter(obj, event)

    def normalize_rect(self, p1, p2):
        sp1 = self.graphics_view.mapToScene(p1)
        sp2 = self.graphics_view.mapToScene(p2)
        left = min(sp1.x(), sp2.x())
        top = min(sp1.y(), sp2.y())
        width = abs(sp1.x() - sp2.x())
        height = abs(sp1.y() - sp2.y())
        return QRectF(left, top, width, height)

    def update_language(self, lang, lm):
        self.label_title.setText(lm.get_text(lang, "IMAGE_EDITOR"))
        self.btn_load.setText(lm.get_text(lang, "LOAD_IMAGE"))
        self.btn_apply_effect.setText(lm.get_text(lang, "APPLY_EFFECT"))
        self.btn_crop.setText(lm.get_text(lang, "CROP_IMAGE"))

# =========================================================
#   RegisterDialog
# =========================================================
class RegisterDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrazione")
        self.setFixedSize(400, 250)
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.label_username = QLabel("Username:")
        layout.addWidget(self.label_username)
        self.edit_username = QLineEdit()
        layout.addWidget(self.edit_username)
        
        self.label_password = QLabel("Password:")
        layout.addWidget(self.label_password)
        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.edit_password)
        
        self.label_password_confirm = QLabel("Conferma Password:")
        layout.addWidget(self.label_password_confirm)
        self.edit_password_confirm = QLineEdit()
        self.edit_password_confirm.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.edit_password_confirm)
        
        btn_layout = QHBoxLayout()
        self.btn_register = QPushButton("Registrati")
        self.btn_register.clicked.connect(self.do_register)
        btn_layout.addWidget(self.btn_register)
        self.btn_cancel = QPushButton("Annulla")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
    
    def do_register(self):
        username = self.edit_username.text().strip()
        password = self.edit_password.text()
        password_confirm = self.edit_password_confirm.text()
        if not username or not password:
            QMessageBox.warning(self, "Errore", "Inserire username e password validi.")
            return
        if password != password_confirm:
            QMessageBox.warning(self, "Errore", "Le password non coincidono.")
            return
        users_data = {}
        if os.path.exists("users.json"):
            try:
                with open("users.json", "r") as f:
                    users_data = json.load(f)
            except:
                pass
        if username in users_data:
            QMessageBox.warning(self, "Errore", "Username già esistente.")
            return
        users_data[username] = password
        try:
            with open("users.json", "w") as f:
                json.dump(users_data, f, indent=2)
            QMessageBox.information(self, "OK", "Registrazione avvenuta con successo!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Non è stato possibile salvare l'utente.\n{str(e)}")
    
    def update_language(self, lang, lm):
        self.setWindowTitle(lm.get_text(lang, "REGISTER_TITLE", default="Registrazione"))
        self.label_username.setText(lm.get_text(lang, "REGISTER_USERNAME", default="Username:"))
        self.label_password.setText(lm.get_text(lang, "REGISTER_PASSWORD", default="Password:"))
        self.label_password_confirm.setText(lm.get_text(lang, "REGISTER_CONFIRM", default="Conferma Password:"))
        self.btn_register.setText(lm.get_text(lang, "REGISTER_BUTTON", default="Registrati"))
        self.btn_cancel.setText(lm.get_text(lang, "CANCEL_BUTTON", default="Annulla"))

# =========================================================
#   LoginDialog
# =========================================================
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setFixedSize(400, 300)
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.title_label = QLabel("ACCEDI")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self.title_label, alignment=Qt.AlignCenter)
        
        self.label_username = QLabel("Username:")
        layout.addWidget(self.label_username)
        self.edit_username = QLineEdit()
        layout.addWidget(self.edit_username)
        
        self.label_password = QLabel("Password:")
        layout.addWidget(self.label_password)
        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.edit_password)
        
        btn_layout = QHBoxLayout()
        self.btn_login = QPushButton("Login")
        self.btn_login.clicked.connect(self.check_credentials)
        btn_layout.addWidget(self.btn_login)
        self.btn_google = QPushButton("Login with Google")
        self.btn_google.clicked.connect(self.login_with_google)
        btn_layout.addWidget(self.btn_google)
        layout.addLayout(btn_layout)
        
        reg_layout = QHBoxLayout()
        self.btn_register = QPushButton("Registrati")
        self.btn_register.clicked.connect(self.open_register_dialog)
        reg_layout.addWidget(self.btn_register)
        layout.addLayout(reg_layout)
        
        self.logged_username = ""
        self.logged_password = ""
    
    def check_credentials(self):
        username = self.edit_username.text()
        password = self.edit_password.text()
        try:
            with open("users.json", "r") as f:
                users = json.load(f)
        except:
            QMessageBox.critical(self, "Errore", "File utenti mancante o corrotto. Prova a registrarti.")
            return
        if username in users and users[username] == password:
            self.logged_username = username
            self.logged_password = password
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", "Username o Password errati.")
    
    def login_with_google(self):
        if InstalledAppFlow is None:
            QMessageBox.warning(self, "Errore", "La libreria google_auth_oauthlib non è installata.")
            return
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secrets.json",
                scopes=["openid", "email", "profile"]
            )
            credentials = flow.run_local_server(port=0)
            user_info = credentials.id_token
            email = user_info.get("email")
            if email:
                self.logged_username = email
                self.logged_password = ""
                QMessageBox.information(self, "Successo", f"Accesso effettuato con Google: {email}")
                self.accept()
            else:
                QMessageBox.warning(self, "Errore", "Impossibile ottenere l'email da Google.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il login con Google: {str(e)}")
    
    def open_register_dialog(self):
        reg_dialog = RegisterDialog()
        reg_dialog.exec_()
    
    def update_language(self, lang, lm):
        self.setWindowTitle(lm.get_text(lang, "LOGIN_TITLE", default="ACCEDI"))
        self.title_label.setText(lm.get_text(lang, "LOGIN_TITLE", default="ACCEDI"))
        self.label_username.setText(lm.get_text(lang, "LOGIN_USERNAME", default="Username:"))
        self.label_password.setText(lm.get_text(lang, "LOGIN_PASSWORD", default="Password:"))
        self.btn_login.setText(lm.get_text(lang, "LOGIN_BUTTON", default="Login"))
        self.btn_register.setText(lm.get_text(lang, "REGISTER_BUTTON", default="Registrati"))
        self.btn_google.setText(lm.get_text(lang, "GOOGLE_LOGIN", default="Login with Google"))

# =========================================================
#   SingleConversionWidget (rimane invariato con update_language)
# =========================================================
class SingleConversionWidget(QWidget):
    def __init__(self, advanced_options):
        super().__init__()
        self.selected_file = None
        self.last_output_file = None
        self.advanced_options = advanced_options
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.label_info = QLabel("Trascina qui un file oppure clicca 'Seleziona File'")
        self.label_info.setStyleSheet("border: 2px dashed #aaa; padding: 30px; color: #000;")
        self.label_info.setAlignment(Qt.AlignCenter)
        self.label_info.setWordWrap(True)
        layout.addWidget(self.label_info)
        
        self.setAcceptDrops(True)
        self.btn_select = QPushButton("Seleziona File")
        self.btn_select.setStyleSheet("color: #000;")
        self.btn_select.clicked.connect(self.select_file)
        layout.addWidget(self.btn_select)
        self.combo_format = QComboBox()
        self.combo_format.setStyleSheet("color: #000;")
        layout.addWidget(self.combo_format)
        self.btn_advanced = QPushButton("Opzioni Avanzate")
        self.btn_advanced.setStyleSheet("color: #000;")
        self.btn_advanced.clicked.connect(self.open_advanced_dialog)
        layout.addWidget(self.btn_advanced)
        
        hbox = QHBoxLayout()
        self.btn_convert = QPushButton("Converti")
        self.btn_convert.setStyleSheet("color: #000;")
        self.btn_convert.clicked.connect(self.do_conversion)
        hbox.addWidget(self.btn_convert)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        hbox.addWidget(self.progress_bar)
        layout.addLayout(hbox)
        self.label_status = QLabel("")
        self.label_status.setWordWrap(True)
        self.label_status.setStyleSheet("color: #000;")
        layout.addWidget(self.label_status)
        self.btn_upload_drive = QPushButton("Carica su Drive")
        self.btn_upload_drive.setStyleSheet("color: #000;")
        self.btn_upload_drive.clicked.connect(self.upload_last_file_to_drive)
        layout.addWidget(self.btn_upload_drive)
    
    def open_advanced_dialog(self):
        dialog = ConversionOptionsDialog(self.advanced_options)
        dialog.exec_()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                self.selected_file = path
                self.label_info.setText(f"File trascinato: {os.path.basename(path)}")
                self.update_formats(path)
            event.acceptProposedAction()
    
    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleziona File", "", "All Files (*.*)")
        if path:
            self.selected_file = path
            self.label_info.setText(f"File selezionato: {os.path.basename(path)}")
            self.update_formats(path)
    
    def update_formats(self, file_path):
        self.combo_format.clear()
        ext = os.path.splitext(file_path)[1].lower()
        formats = []
        if ext == ".docx":
            formats = [".pdf", ".pages", ".txt"]
        elif ext == ".pdf":
            formats = [".docx", ".pages", ".txt"]
        elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]:
            formats = [".jpg", ".png", ".pdf", ".webp"]
        elif ext == ".svg":
            formats = [".svg", ".pdf", ".png", ".jpg", ".webp"]
        if formats:
            for f in formats:
                self.combo_format.addItem(f)
        else:
            self.combo_format.addItem("Formato non supportato")
    
    def do_conversion(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Attenzione", "Nessun file selezionato!")
            return
        out_ext = self.combo_format.currentText()
        if out_ext == "Formato non supportato":
            QMessageBox.warning(self, "Attenzione", "Formato non supportato!")
            return
        in_path = self.selected_file
        base, _ = os.path.splitext(in_path)
        out_path = base + out_ext
        
        def conversion_worker():
            try:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.do_actual_conversion(in_path, out_path)
                for i in range(1, 101, 10):
                    time.sleep(0.05)
                    self.progress_bar.setValue(i)
                self.progress_bar.setVisible(False)
                self.label_status.setText(f"Convertito in: {out_path}")
                self.last_output_file = out_path
            except Exception as e:
                self.progress_bar.setVisible(False)
                mbox = QMessageBox()
                mbox.setWindowTitle("Errore Conversione")
                mbox.setText(str(e))
                mbox.setStyleSheet("QLabel{ color: black; }")
                mbox.exec_()
        t = threading.Thread(target=conversion_worker)
        t.start()
    
    def do_actual_conversion(self, in_path, out_path):
        ext_in = os.path.splitext(in_path)[1].lower()
        ext_out = os.path.splitext(out_path)[1].lower()
        pdf_rotation = self.advanced_options.get("pdf_rotation", 0)
        pdf_delete_even = self.advanced_options.get("pdf_delete_even", False)
        img_quality = self.advanced_options.get("img_quality", 80)
        img_dpi = self.advanced_options.get("img_dpi", 300)
        if ext_in == ".docx" and ext_out == ".pdf":
            convert_docx_to_pdf(in_path, out_path)
        elif ext_in == ".docx" and ext_out == ".pages":
            temp_pdf = convert_docx_to_pdf(in_path)
            convert_pdf_to_pages(temp_pdf, out_path)
        elif ext_in == ".docx" and ext_out == ".txt":
            convert_docx_to_txt(in_path, out_path)
        elif ext_in == ".pdf" and ext_out == ".docx":
            convert_pdf_to_docx(in_path, out_path)
        elif ext_in == ".pdf" and ext_out == ".pages":
            convert_pdf_to_pages(in_path, out_path)
        elif ext_in == ".pdf" and ext_out == ".txt":
            convert_pdf_to_txt(in_path, out_path)
        else:
            convert_image(in_path, out_path)
    
    def upload_last_file_to_drive(self):
        if not self.last_output_file:
            QMessageBox.warning(self, "Attenzione", "Non hai ancora creato nessun file da caricare!")
            return
        if not os.path.exists(self.last_output_file):
            QMessageBox.warning(self, "Attenzione", "Il file creato non esiste più!")
            return
        try:
            msg = upload_to_drive(self.last_output_file)
            mbox = QMessageBox()
            mbox.setWindowTitle("Upload Drive")
            mbox.setText(msg)
            mbox.setStyleSheet("QLabel{ color: black; }")
            mbox.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Errore Upload Drive", str(e))
    
    def update_language(self, lang, lm):
        self.label_info.setText(lm.get_text(lang, "SINGLE_INFO"))
        self.btn_select.setText(lm.get_text(lang, "SELECT_FILE"))
        self.btn_advanced.setText(lm.get_text(lang, "ADVANCED_OPTIONS"))
        self.btn_convert.setText(lm.get_text(lang, "CONVERT_BUTTON"))
        self.btn_upload_drive.setText(lm.get_text(lang, "UPLOAD_DRIVE"))

# =========================================================
#   MergePDFWidget (rimane invariato con update_language)
# =========================================================
class MergePDFWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.label_info = QLabel("Trascina qui i file PDF da unire oppure usa 'Aggiungi PDF'")
        self.label_info.setWordWrap(True)
        self.label_info.setStyleSheet("border: 2px dashed #aaa; padding: 20px; color: #000;")
        self.label_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_info)
        self.setAcceptDrops(True)
        self.list_merge = QListWidget()
        self.list_merge.setStyleSheet("color: #000;")
        layout.addWidget(self.list_merge)
        hbox = QHBoxLayout()
        self.btn_add = QPushButton("Aggiungi PDF")
        self.btn_add.setStyleSheet("color: #000;")
        self.btn_add.clicked.connect(self.add_pdf)
        hbox.addWidget(self.btn_add)
        self.btn_up = QPushButton("Su")
        self.btn_up.setStyleSheet("color: #000;")
        self.btn_up.clicked.connect(self.move_item_up)
        hbox.addWidget(self.btn_up)
        self.btn_down = QPushButton("Giù")
        self.btn_down.setStyleSheet("color: #000;")
        self.btn_down.clicked.connect(self.move_item_down)
        hbox.addWidget(self.btn_down)
        layout.addLayout(hbox)
        self.btn_merge = QPushButton("Unisci PDF")
        self.btn_merge.setStyleSheet("color: #000;")
        self.btn_merge.clicked.connect(self.do_merge)
        layout.addWidget(self.btn_merge)
        self.label_status = QLabel("")
        self.label_status.setWordWrap(True)
        self.label_status.setStyleSheet("color: #000;")
        layout.addWidget(self.label_status)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith(".pdf"):
                    self.list_merge.addItem(path)
            event.acceptProposedAction()
    
    def add_pdf(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleziona PDF", "", "PDF Files (*.pdf)")
        if files:
            for f in files:
                self.list_merge.addItem(f)
    
    def move_item_up(self):
        row = self.list_merge.currentRow()
        if row > 0:
            item = self.list_merge.takeItem(row)
            self.list_merge.insertItem(row - 1, item)
            self.list_merge.setCurrentRow(row - 1)
    
    def move_item_down(self):
        row = self.list_merge.currentRow()
        if row < self.list_merge.count() - 1 and row >= 0:
            item = self.list_merge.takeItem(row)
            self.list_merge.insertItem(row + 1, item)
            self.list_merge.setCurrentRow(row + 1)
    
    def do_merge(self):
        n = self.list_merge.count()
        if n < 2:
            QMessageBox.warning(self, "Attenzione", "Aggiungi almeno 2 PDF per unirli.")
            return
        pdf_list = [self.list_merge.item(i).text() for i in range(n)]
        out_path, _ = QFileDialog.getSaveFileName(self, "Salva PDF unito", "", "PDF Files (*.pdf)")
        if not out_path:
            return
        try:
            merge_pdfs(pdf_list, out_path)
            self.label_status.setText(f"PDF uniti in: {out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore Merge PDF", str(e))
    
    def update_language(self, lang, lm):
        self.label_info.setText(lm.get_text(lang, "MERGE_INFO"))
        self.btn_add.setText(lm.get_text(lang, "ADD_PDF"))
        self.btn_up.setText(lm.get_text(lang, "MOVE_UP"))
        self.btn_down.setText(lm.get_text(lang, "MOVE_DOWN"))
        self.btn_merge.setText(lm.get_text(lang, "MERGE_BUTTON"))

# =========================================================
#   SplitPDFWidget (rimane invariato con update_language)
# =========================================================
class SplitPDFWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_pdf = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.label_info = QLabel("Trascina qui un PDF oppure usa 'Seleziona PDF'")
        self.label_info.setWordWrap(True)
        self.label_info.setStyleSheet("border: 2px dashed #aaa; padding: 20px; color: #000;")
        self.label_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_info)
        self.setAcceptDrops(True)
        self.btn_select = QPushButton("Seleziona PDF")
        self.btn_select.setStyleSheet("color: #000;")
        self.btn_select.clicked.connect(self.select_pdf)
        layout.addWidget(self.btn_select)
        self.label_selected = QLabel("Nessun PDF selezionato")
        self.label_selected.setWordWrap(True)
        self.label_selected.setStyleSheet("color: #000;")
        layout.addWidget(self.label_selected)
        self.line_pages = QLineEdit()
        self.line_pages.setPlaceholderText("Intervalli di pagine (es. 1-3,5,7-9)")
        self.line_pages.setStyleSheet("color: #000;")
        layout.addWidget(self.line_pages)
        self.btn_split = QPushButton("Estrai Pagine")
        self.btn_split.setStyleSheet("color: #000;")
        self.btn_split.clicked.connect(self.do_split)
        layout.addWidget(self.btn_split)
        self.label_status = QLabel("")
        self.label_status.setWordWrap(True)
        self.label_status.setStyleSheet("color: #000;")
        layout.addWidget(self.label_status)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if path.lower().endswith(".pdf"):
                    self.selected_pdf = path
                    self.label_info.setText(f"File trascinato: {os.path.basename(path)}")
                    self.label_selected.setText(f"PDF: {os.path.basename(path)}")
            event.acceptProposedAction()
    
    def select_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleziona PDF", "", "PDF Files (*.pdf)")
        if path:
            self.selected_pdf = path
            self.label_info.setText(f"File selezionato: {os.path.basename(path)}")
            self.label_selected.setText(f"PDF: {os.path.basename(path)}")
    
    def do_split(self):
        if not self.selected_pdf:
            QMessageBox.warning(self, "Attenzione", "Seleziona un PDF!")
            return
        pages_string = self.line_pages.text().strip()
        if not pages_string:
            QMessageBox.warning(self, "Attenzione", "Inserisci gli intervalli di pagine!")
            return
        out_path, _ = QFileDialog.getSaveFileName(self, "Salva PDF estratto", "", "PDF Files (*.pdf)")
        if not out_path:
            return
        try:
            split_pdf(self.selected_pdf, out_path, pages_string)
            self.label_status.setText(f"PDF estratto in: {out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore Split PDF", str(e))
    
    def update_language(self, lang, lm):
        self.label_info.setText(lm.get_text(lang, "SPLIT_INFO"))
        self.btn_select.setText(lm.get_text(lang, "SELECT_PDF"))
        self.line_pages.setPlaceholderText(lm.get_text(lang, "EXTRACT_PAGES"))
        self.btn_split.setText(lm.get_text(lang, "EXTRACT_PAGES"))

# =========================================================
#   MainWindow
# =========================================================
class MainWindow(QMainWindow):
    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password
        self.current_theme = "light"
        self.nav_visible = True
        self.advanced_options = {}
        self.language_manager = LanguageManager()
        self.current_lang = "it"
        self.setWindowTitle("Universal Converter - Navigation Menu")
        self.setMinimumSize(1000, 600)
        self.last_output_file = None
        
        # Toolbar
        self.toolbar = QToolBar("Menu")
        self.addToolBar(self.toolbar)
        self.hamburger_btn = QPushButton("☰")
        self.hamburger_btn.setStyleSheet("background-color: #cccccc; border: none; font-size: 20px; color: #000;")
        self.hamburger_btn.clicked.connect(self.toggle_nav)
        self.toolbar.addWidget(self.hamburger_btn)
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setStyleSheet("background-color: #cccccc; border: none; font-size: 20px; color: #000;")
        self.btn_settings.clicked.connect(self.open_options_dialog)
        self.toolbar.addWidget(self.btn_settings)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Nav panel
        self.nav_panel = QWidget()
        self.nav_panel.setMinimumWidth(0)
        self.nav_panel.setMaximumWidth(200)
        nav_layout = QVBoxLayout()
        self.nav_panel.setLayout(nav_layout)
        self.nav_panel.setStyleSheet("background-color: #cccccc; color: #000;")
        
        self.btn_single = QPushButton()
        self.btn_single.setObjectName("menuButton")
        self.btn_single.clicked.connect(lambda: self.switch_page(0))
        nav_layout.addWidget(self.btn_single)
        
        self.btn_merge = QPushButton()
        self.btn_merge.setObjectName("menuButton")
        self.btn_merge.clicked.connect(lambda: self.switch_page(1))
        nav_layout.addWidget(self.btn_merge)
        
        self.btn_split = QPushButton()
        self.btn_split.setObjectName("menuButton")
        self.btn_split.clicked.connect(lambda: self.switch_page(2))
        nav_layout.addWidget(self.btn_split)
        
        self.btn_image_editor = QPushButton()
        self.btn_image_editor.setObjectName("menuButton")
        self.btn_image_editor.clicked.connect(lambda: self.switch_page(3))
        nav_layout.addWidget(self.btn_image_editor)
        
        self.btn_options = QPushButton()
        self.btn_options.setObjectName("menuButton")
        self.btn_options.clicked.connect(self.open_options_dialog)
        nav_layout.addWidget(self.btn_options)
        
        nav_layout.addStretch()
        
        # Icona utente + nome + Logout
        user_layout = QHBoxLayout()
        self.label_user_icon = QLabel("👤")
        self.label_user_icon.setStyleSheet("font-size: 20px;")
        user_layout.addWidget(self.label_user_icon)
        self.label_user_name = QLabel(self.username)
        user_layout.addWidget(self.label_user_name)
        nav_layout.addLayout(user_layout)
        
        self.btn_logout = QPushButton()
        self.btn_logout.setObjectName("menuButton")
        self.btn_logout.clicked.connect(self.do_logout)
        nav_layout.addWidget(self.btn_logout)
        
        # StackedWidget
        self.stack = QStackedWidget()
        self.page_single = SingleConversionWidget(self.advanced_options)
        self.page_merge = MergePDFWidget()
        self.page_split = SplitPDFWidget()
        self.page_image_editor = ImageEditorWidget()
        self.stack.addWidget(self.page_single)
        self.stack.addWidget(self.page_merge)
        self.stack.addWidget(self.page_split)
        self.stack.addWidget(self.page_image_editor)
        
        main_layout.addWidget(self.nav_panel)
        main_layout.addWidget(self.stack)
        
        self.apply_theme()
        self.apply_language()
        self.update_menu_styles()

    # --------------------------------------------------------
    # SEZIONE: Metodi di login persistente
    # --------------------------------------------------------
    def do_logout(self):
        # Cancella il login persistente
        clear_login()
        self.close()   # Chiude la MainWindow

        from gui import LoginDialog  # Se LoginDialog è nello stesso file potresti non aver bisogno di import
        login = LoginDialog()
        if login.exec_() == QDialog.Accepted:
            # Se l'utente fa di nuovo login
            save_login(login.logged_username)
            new_main = MainWindow(login.logged_username, login.logged_password)
            new_main.show()

    # --------------------------------------------------------
    # FINE SEZIONE: Metodi di login persistente
    # --------------------------------------------------------

    def toggle_nav(self):
        animation = QPropertyAnimation(self.nav_panel, b"maximumWidth")
        animation.setDuration(300)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        if self.nav_visible:
            animation.setStartValue(self.nav_panel.maximumWidth())
            animation.setEndValue(0)
            self.nav_visible = False
        else:
            animation.setStartValue(0)
            animation.setEndValue(200)
            self.nav_visible = True
        animation.start()
        self.current_animation = animation
    
    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        self.update_menu_styles()
    
    def update_menu_styles(self):
        buttons = [self.btn_single, self.btn_merge, self.btn_split, self.btn_image_editor]
        for idx, btn in enumerate(buttons):
            if self.stack.currentIndex() == idx:
                btn.setProperty("selected", "true")
            else:
                btn.setProperty("selected", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    def open_options_dialog(self):
        dlg = OptionsDialog(self.current_lang, self.current_theme, self.username)
        if dlg.exec_() == QDialog.Accepted:
            self.current_lang = dlg.combo_language.currentData()
            self.current_theme = dlg.combo_theme.currentData()
            self.apply_theme()
            self.apply_language()
    
    def apply_theme(self):
        if self.current_theme == "light":
            self.setStyleSheet("""
                QMainWindow { background-color: white; }
                QWidget { background-color: white; color: #007BFF; }
                QPushButton { 
                    background-color: white; 
                    color: #007BFF; 
                    border: 1px solid #007BFF;
                    padding: 8px;
                }
                QPushButton:hover#menuButton { 
                    background-color: #cce5ff; 
                }
                QPushButton#menuButton[selected="true"] {
                    background-color: #0056b3;
                    color: white;
                }
                QLineEdit, QComboBox { 
                    background-color: white; 
                    color: #007BFF; 
                    border: 1px solid #007BFF;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #333333; }
                QWidget { background-color: #333333; color: #FFA500; }
                QPushButton { 
                    background-color: #333333; 
                    color: #FFA500; 
                    border: 1px solid #FFA500;
                    padding: 8px;
                }
                QPushButton:hover#menuButton { 
                    background-color: #ff8c00; 
                }
                QPushButton#menuButton[selected="true"] {
                    background-color: #e69500;
                    color: white;
                }
                QLineEdit, QComboBox { 
                    background-color: #333333; 
                    color: #FFA500; 
                    border: 1px solid #FFA500;
                }
            """)
    
    def apply_language(self):
        lm = self.language_manager
        lang = self.current_lang
        
        self.btn_single.setText(lm.get_text(lang, "MENU_SINGLE"))
        self.btn_merge.setText(lm.get_text(lang, "MENU_MERGE"))
        self.btn_split.setText(lm.get_text(lang, "MENU_SPLIT"))
        self.btn_image_editor.setText(lm.get_text(lang, "IMAGE_EDITOR"))
        self.btn_options.setText(lm.get_text(lang, "OPTIONS"))
        self.btn_logout.setText(lm.get_text(lang, "LOGOUT"))
        self.label_user_icon.setText("👤")
        self.label_user_name.setText(self.username)
        
        if hasattr(self.page_single, "update_language"):
            self.page_single.update_language(lang, lm)
        if hasattr(self.page_merge, "update_language"):
            self.page_merge.update_language(lang, lm)
        if hasattr(self.page_split, "update_language"):
            self.page_split.update_language(lang, lm)
        if hasattr(self.page_image_editor, "update_language"):
            self.page_image_editor.update_language(lang, lm)
    
    def upload_last_file_to_drive(self):
        last_file = self.page_single.last_output_file
        if not last_file:
            QMessageBox.warning(self, "Attenzione", "Non hai ancora creato nessun file da caricare!")
            return
        if not os.path.exists(last_file):
            QMessageBox.warning(self, "Attenzione", "Il file creato non esiste più!")
            return
        try:
            msg = upload_to_drive(last_file)
            mbox = QMessageBox()
            mbox.setWindowTitle("Upload Drive")
            mbox.setText(msg)
            mbox.setStyleSheet("QLabel{ color: black; }")
            mbox.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Errore Upload Drive", str(e))