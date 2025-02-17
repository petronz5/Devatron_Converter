import os
DESKTOP_DIR = os.path.join(os.path.expanduser("~"), "Desktop")
import json
import threading
import time

import tempfile
from history import log_conversion  # <--- IMPORT con la nuova firma
from PyQt5.QtCore import QSettings, QDateTime, Qt, QPropertyAnimation, QEasingCurve, QRectF, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor, QKeySequence, QTransform
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QFileDialog, QComboBox, QMessageBox, QListWidget, QLineEdit, QProgressBar,
    QStackedWidget, QDialog, QToolBar, QTabWidget, QSpinBox, QFormLayout, QCheckBox,
    QSlider, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem,
    QListWidgetItem, QShortcut, QTextEdit
)

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    InstalledAppFlow = None

from conversions import (
    convert_docx_to_pdf, convert_pdf_to_docx, convert_docx_to_txt, convert_pdf_to_txt,
    convert_image, merge_pdfs, convert_pdf_to_pages, split_pdf,
    compress_folder, decompress_zip
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
        # login valido per 30 giorni
        if current - login_date < 30 * 24 * 3600:
            return username
    return None

def clear_login():
    settings = QSettings("MyCompany", "ConverterApp")
    settings.clear()

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.setMinimumSize(500, 400)
        layout = QVBoxLayout(self)

        help_text = (
            "Benvenuto in Universal Converter!\n\n"
            "Funzionalità principali:\n"
            "- Conversione di documenti, PDF e immagini.\n"
            "- Unione e divisione di file PDF.\n"
            "- Modifica e ritaglio di immagini.\n\n"
            "Scorciatoie da tastiera:\n"
            "  Command + 1: Singola Conversione\n"
            "  Command + 2: Unisci PDF\n"
            "  Command + 3: Estrai Pagine PDF\n"
            "  Command + 4: Editor di Immagine\n"
            "  Command + 5: Cronologia\n\n"
            "Per ulteriori informazioni, consulta la documentazione online."
        )

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(help_text)
        layout.addWidget(text_edit)

        btn_close = QPushButton("Chiudi")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


# =========================================================
#   LanguageManager
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
                "SINGLE_INFO": "Trascina qui i file oppure clicca 'Aggiungi File'",
                "SELECT_FILE": "Aggiungi File",
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
                "USER_ICON": "Utente: ",
                "MENU_SINGLE": "Singola Conversione",
                "MENU_MERGE": "Unisci PDF",
                "MENU_SPLIT": "Estrai Pagine PDF",
                "MENU_HISTORY": "Cronologia",
                "HISTORY_TITLE": "Cronologia Conversioni",
                "REFRESH_HISTORY": "Aggiorna"
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
                "THEME_SWITCH": "Switch Theme",
                "USER_INFO": "Name: {username}\nPassword: {password}",
                "SWITCH_TO_DARK": "Switch to Dark Theme",
                "SWITCH_TO_LIGHT": "Switch to Light Theme",
                "GOOGLE_LOGIN": "Login with Google",
                "OPTIONS": "Options",
                "OPT_TAB_LANGUAGE": "Language",
                "OPT_TAB_THEME": "Theme",
                "OPT_TAB_USER": "User",
                "OPT_LANGUAGE": "Change Language",
                "OPT_THEME": "Select Theme",
                "OPT_THEME_CHOICE": "Theme:",
                "OPT_USER_CHANGE": "Change Password",
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
                "USER_ICON": "User: ",
                "MENU_SINGLE": "Single Conversion",
                "MENU_MERGE": "Merge PDF",
                "MENU_SPLIT": "Split PDF",
                "MENU_HISTORY": "History",
                "HISTORY_TITLE": "Conversion History",
                "REFRESH_HISTORY": "Refresh"
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
                "SINGLE_INFO": "Arrastra un archivo aquí o haz clic en 'Seleccionar Archivo'",
                "SELECT_FILE": "Seleccionar Archivo",
                "ADVANCED_OPTIONS": "Opciones Avanzadas",
                "CONVERT_BUTTON": "Convertir",
                "UPLOAD_DRIVE": "Subir a Drive",
                "MERGE_INFO": "Arrastra los archivos PDF para unir o haz clic en 'Agregar PDF'",
                "ADD_PDF": "Agregar PDF",
                "MOVE_UP": "Subir",
                "MOVE_DOWN": "Bajar",
                "MERGE_BUTTON": "Unir PDF",
                "SPLIT_INFO": "Arrastra un PDF aquí o haz clic en 'Seleccionar PDF'",
                "SELECT_PDF": "Seleccionar PDF",
                "EXTRACT_PAGES": "Extraer Páginas",
                "SETTINGS_TITLE": "Configuración",
                "LANGUAGE_LABEL": "Selecciona Idioma:",
                "THEME_SWITCH": "Cambiar Tema",
                "USER_INFO": "Nombre: {username}\nContraseña: {password}",
                "SWITCH_TO_DARK": "Cambiar a Tema Oscuro",
                "SWITCH_TO_LIGHT": "Cambiar a Tema Claro",
                "GOOGLE_LOGIN": "Iniciar sesión con Google",
                "OPTIONS": "Opciones",
                "OPT_TAB_LANGUAGE": "Idioma",
                "OPT_TAB_THEME": "Tema",
                "OPT_TAB_USER": "Usuario",
                "OPT_LANGUAGE": "Cambiar Idioma",
                "OPT_THEME": "Selecciona Tema",
                "OPT_THEME_CHOICE": "Tema:",
                "OPT_USER_CHANGE": "Cambiar Contraseña",
                "NEW_PASSWORD": "Nueva Contraseña:",
                "CONFIRM_PASSWORD": "Confirmar Contraseña:",
                "UPDATE_PASSWORD": "Actualizar Contraseña",
                "PASSWORD_UPDATED": "¡Contraseña actualizada con éxito!",
                "LOGOUT": "Cerrar sesión",
                "IMAGE_EDITOR": "Editor de Imágenes",
                "LOAD_IMAGE": "Cargar Imagen",
                "SCALE_IMAGE": "Escalar Imagen",
                "CROP_IMAGE": "Recortar",
                "APPLY_EFFECT": "Aplicar Efecto (B/N)",
                "USER_ICON": "Usuario: ",
                "MENU_SINGLE": "Conversión Única",
                "MENU_MERGE": "Unir PDF",
                "MENU_SPLIT": "Dividir PDF",
                "MENU_HISTORY": "Historial",
                "HISTORY_TITLE": "Historial de Conversiones",
                "REFRESH_HISTORY": "Actualizar"
            },
            "fr": {
                "LOGIN_TITLE": "CONNEXION",
                "LOGIN_USERNAME": "Nom d'utilisateur:",
                "LOGIN_PASSWORD": "Mot de passe:",
                "LOGIN_BUTTON": "Se connecter",
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
                "MERGE_INFO": "Glissez les fichiers PDF à fusionner ou cliquez sur 'Ajouter PDF'",
                "ADD_PDF": "Ajouter PDF",
                "MOVE_UP": "Monter",
                "MOVE_DOWN": "Descendre",
                "MERGE_BUTTON": "Fusionner PDF",
                "SPLIT_INFO": "Glissez un PDF ici ou cliquez sur 'Sélectionner PDF'",
                "SELECT_PDF": "Sélectionner PDF",
                "EXTRACT_PAGES": "Extraire les pages",
                "SETTINGS_TITLE": "Paramètres",
                "LANGUAGE_LABEL": "Sélectionnez la langue:",
                "THEME_SWITCH": "Changer de thème",
                "USER_INFO": "Nom: {username}\nMot de passe: {password}",
                "SWITCH_TO_DARK": "Passer au thème sombre",
                "SWITCH_TO_LIGHT": "Passer au thème clair",
                "GOOGLE_LOGIN": "Se connecter avec Google",
                "OPTIONS": "Options",
                "OPT_TAB_LANGUAGE": "Langue",
                "OPT_TAB_THEME": "Thème",
                "OPT_TAB_USER": "Utilisateur",
                "OPT_LANGUAGE": "Changer la langue",
                "OPT_THEME": "Sélectionner le thème",
                "OPT_THEME_CHOICE": "Thème:",
                "OPT_USER_CHANGE": "Changer le mot de passe",
                "NEW_PASSWORD": "Nouveau mot de passe:",
                "CONFIRM_PASSWORD": "Confirmer le mot de passe:",
                "UPDATE_PASSWORD": "Mettre à jour le mot de passe",
                "PASSWORD_UPDATED": "Mot de passe mis à jour avec succès!",
                "LOGOUT": "Déconnexion",
                "IMAGE_EDITOR": "Éditeur d'images",
                "LOAD_IMAGE": "Charger l'image",
                "SCALE_IMAGE": "Redimensionner l'image",
                "CROP_IMAGE": "Recadrer",
                "APPLY_EFFECT": "Appliquer l'effet (N/B)",
                "USER_ICON": "Utilisateur: ",
                "MENU_SINGLE": "Conversion Unique",
                "MENU_MERGE": "Fusionner PDF",
                "MENU_SPLIT": "Diviser PDF",
                "MENU_HISTORY": "Historique",
                "HISTORY_TITLE": "Historique des conversions",
                "REFRESH_HISTORY": "Rafraîchir"
            },
            "de": {
                "LOGIN_TITLE": "ANMELDUNG",
                "LOGIN_USERNAME": "Benutzername:",
                "LOGIN_PASSWORD": "Passwort:",
                "LOGIN_BUTTON": "Anmelden",
                "REGISTER_BUTTON": "Registrieren",
                "REGISTER_TITLE": "Registrierung",
                "REGISTER_USERNAME": "Benutzername:",
                "REGISTER_PASSWORD": "Passwort:",
                "REGISTER_CONFIRM": "Passwort bestätigen:",
                "OLD_PASSWORD": "Altes Passwort:",
                "CANCEL_BUTTON": "Abbrechen",
                "SINGLE_INFO": "Ziehen Sie eine Datei hierher oder klicken Sie auf 'Datei auswählen'",
                "SELECT_FILE": "Datei auswählen",
                "ADVANCED_OPTIONS": "Erweiterte Optionen",
                "CONVERT_BUTTON": "Konvertieren",
                "UPLOAD_DRIVE": "Auf Drive hochladen",
                "MERGE_INFO": "Ziehen Sie PDF-Dateien hierher, um sie zusammenzuführen, oder klicken Sie auf 'PDF hinzufügen'",
                "ADD_PDF": "PDF hinzufügen",
                "MOVE_UP": "Nach oben",
                "MOVE_DOWN": "Nach unten",
                "MERGE_BUTTON": "PDF zusammenführen",
                "SPLIT_INFO": "Ziehen Sie eine PDF hierher oder klicken Sie auf 'PDF auswählen'",
                "SELECT_PDF": "PDF auswählen",
                "EXTRACT_PAGES": "Seiten extrahieren",
                "SETTINGS_TITLE": "Einstellungen",
                "LANGUAGE_LABEL": "Sprache auswählen:",
                "THEME_SWITCH": "Thema wechseln",
                "USER_INFO": "Name: {username}\nPasswort: {password}",
                "SWITCH_TO_DARK": "Zum dunklen Thema wechseln",
                "SWITCH_TO_LIGHT": "Zum hellen Thema wechseln",
                "GOOGLE_LOGIN": "Mit Google anmelden",
                "OPTIONS": "Optionen",
                "OPT_TAB_LANGUAGE": "Sprache",
                "OPT_TAB_THEME": "Thema",
                "OPT_TAB_USER": "Benutzer",
                "OPT_LANGUAGE": "Sprache ändern",
                "OPT_THEME": "Thema auswählen",
                "OPT_THEME_CHOICE": "Thema:",
                "OPT_USER_CHANGE": "Passwort ändern",
                "NEW_PASSWORD": "Neues Passwort:",
                "CONFIRM_PASSWORD": "Passwort bestätigen:",
                "UPDATE_PASSWORD": "Passwort aktualisieren",
                "PASSWORD_UPDATED": "Passwort erfolgreich aktualisiert!",
                "LOGOUT": "Abmelden",
                "IMAGE_EDITOR": "Bildeditor",
                "LOAD_IMAGE": "Bild laden",
                "SCALE_IMAGE": "Bild skalieren",
                "CROP_IMAGE": "Zuschneiden",
                "APPLY_EFFECT": "Effekt anwenden (SW)",
                "USER_ICON": "Benutzer: ",
                "MENU_SINGLE": "Einzelkonvertierung",
                "MENU_MERGE": "PDF zusammenführen",
                "MENU_SPLIT": "PDF aufteilen",
                "MENU_HISTORY": "Verlauf",
                "HISTORY_TITLE": "Konvertierungshistorie",
                "REFRESH_HISTORY": "Aktualisieren"
            }
        }

    def get_text(self, lang, key, default=None, **kwargs):
        if lang not in self.translations:
            lang = "it"
        text = self.translations[lang].get(key, default if default else key)
        if kwargs:
            text = text.format(**kwargs)
        return text


class FileListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def keyPressEvent(self, event):
        # Se l'utente preme Delete o Backspace, richiede al genitore (che dovrà avere il metodo remove_selected_files)
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            if self.parent() is not None and hasattr(self.parent(), "remove_selected_files"):
                self.parent().remove_selected_files()
        else:
            super().keyPressEvent(event)

# =========================================================
#   OptionsDialog
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
        lang_label = QLabel(self.lm.get_text(self.language, "OPT_LANGUAGE", default="Cambia lingua"))
        lang_layout.addWidget(lang_label)
        self.combo_language = QComboBox()
        self.combo_language.addItem("Italiano (it)", "it")
        self.combo_language.addItem("English (en)", "en")
        self.combo_language.addItem("Español (es)", "es")
        self.combo_language.addItem("Français (fr)", "fr")
        self.combo_language.addItem("Deutsch (de)", "de")
        index = self.combo_language.findData(self.language)
        if index >= 0:
            self.combo_language.setCurrentIndex(index)
        lang_layout.addWidget(self.combo_language)
        tab_widget.addTab(lang_tab, self.lm.get_text(self.language, "OPT_TAB_LANGUAGE", default="Lingua"))
        
        # Scheda Tema
        theme_tab = QWidget()
        theme_layout = QVBoxLayout()
        theme_tab.setLayout(theme_layout)
        theme_label = QLabel(self.lm.get_text(self.language, "OPT_THEME", default="Seleziona tema"))
        theme_layout.addWidget(theme_label)
        self.combo_theme = QComboBox()
        self.combo_theme.addItem("Chiaro", "light")
        self.combo_theme.addItem("Scuro", "dark")
        idx = self.combo_theme.findData(self.theme)
        if idx >= 0:
            self.combo_theme.setCurrentIndex(idx)
        theme_layout.addWidget(self.combo_theme)
        tab_widget.addTab(theme_tab, self.lm.get_text(self.language, "OPT_TAB_THEME", default="Tema"))
        
        # Scheda Utente (cambio password)
        user_tab = QWidget()
        user_layout = QFormLayout()
        user_tab.setLayout(user_layout)
        self.label_current_user = QLabel(self.username)
        user_layout.addRow(self.lm.get_text(self.language, "USER_ICON", default="Utente:"), self.label_current_user)
        
        # Campo vecchia password
        self.edit_old_password = QLineEdit()
        self.edit_old_password.setEchoMode(QLineEdit.Password)
        user_layout.addRow(self.lm.get_text(self.language, "OLD_PASSWORD", default="Vecchia Password:"), self.edit_old_password)
        
        # Campo nuova password + occhiello
        self.edit_new_password = QLineEdit()
        self.edit_new_password.setEchoMode(QLineEdit.Password)
        self.btn_eye_new = QPushButton("👁")
        self.btn_eye_new.setCheckable(True)
        self.btn_eye_new.toggled.connect(self.toggle_new_password)
        hbox_new = QHBoxLayout()
        hbox_new.addWidget(self.edit_new_password)
        hbox_new.addWidget(self.btn_eye_new)
        user_layout.addRow(self.lm.get_text(self.language, "NEW_PASSWORD", default="Nuova Password:"), hbox_new)
        
        # Campo conferma password + occhiello
        self.edit_confirm_password = QLineEdit()
        self.edit_confirm_password.setEchoMode(QLineEdit.Password)
        self.btn_eye_confirm = QPushButton("👁")
        self.btn_eye_confirm.setCheckable(True)
        self.btn_eye_confirm.toggled.connect(self.toggle_confirm_password)
        hbox_conf = QHBoxLayout()
        hbox_conf.addWidget(self.edit_confirm_password)
        hbox_conf.addWidget(self.btn_eye_confirm)
        user_layout.addRow(self.lm.get_text(self.language, "CONFIRM_PASSWORD", default="Conferma Password:"), hbox_conf)
        
        self.btn_update_password = QPushButton(self.lm.get_text(self.language, "UPDATE_PASSWORD", default="Aggiorna Password"))
        self.btn_update_password.clicked.connect(self.update_password)
        user_layout.addRow(self.btn_update_password)
        tab_widget.addTab(user_tab, self.lm.get_text(self.language, "OPT_TAB_USER", default="Utente"))
        
        # Pulsanti OK/Cancel
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton(self.lm.get_text(self.language, "CANCEL_BUTTON", default="Annulla"))
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
            QMessageBox.information(self, "OK", self.lm.get_text(self.language, "PASSWORD_UPDATED", default="Password aggiornata con successo!"))
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante l'aggiornamento della password:\n{str(e)}")

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

# =========================================================
#   ConversionOptionsDialog (facoltativo, se già presente)
#   - Qui vengono gestite opzioni avanzate come rotazione PDF, DPI immagini, ecc.
# =========================================================
class ConversionOptionsDialog(QDialog):
    def __init__(self, advanced_options):
        super().__init__()
        self.setWindowTitle("Opzioni Avanzate")
        self.advanced_options = advanced_options
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Esempio: campi per pdf_rotation, pdf_delete_even, img_quality, ecc.
        # ...
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)
    
    def accept(self):
        # Salva eventuali modifiche a self.advanced_options
        super().accept()

# =========================================================
#   ImageEditorWidget
# =========================================================
class ImageEditorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.original_pixmap = None  # Per gestire l'undo
        self.current_pixmap = None
        self.crop_rect_item = None
        self.is_selecting = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.label_title = QLabel("Modifica Immagine")
        layout.addWidget(self.label_title)

        # Barra dei pulsanti per funzioni base e aggiuntive
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

        # Pulsanti di rotazione
        self.btn_rotate_left = QPushButton("Ruota Sinistra")
        self.btn_rotate_left.clicked.connect(lambda: self.rotate_image(-90))
        hbox_btn.addWidget(self.btn_rotate_left)

        self.btn_rotate_right = QPushButton("Ruota Destra")
        self.btn_rotate_right.clicked.connect(lambda: self.rotate_image(90))
        hbox_btn.addWidget(self.btn_rotate_right)

        # Pulsante di Undo
        self.btn_undo = QPushButton("Annulla")
        self.btn_undo.clicked.connect(self.undo)
        hbox_btn.addWidget(self.btn_undo)

        layout.addLayout(hbox_btn)

        # Slider per lo scaling (già presente)
        self.slider_scale = QSlider(Qt.Horizontal)
        self.slider_scale.setRange(1, 300)
        self.slider_scale.setValue(100)
        self.slider_scale.valueChanged.connect(self.scale_image)
        layout.addWidget(self.slider_scale)

        # Nuovi slider per luminosità e contrasto
        self.slider_brightness = QSlider(Qt.Horizontal)
        self.slider_brightness.setRange(-100, 100)
        self.slider_brightness.setValue(0)
        self.slider_brightness.valueChanged.connect(self.adjust_brightness)
        layout.addWidget(QLabel("Luminosità"))
        layout.addWidget(self.slider_brightness)

        self.slider_contrast = QSlider(Qt.Horizontal)
        self.slider_contrast.setRange(-100, 100)
        self.slider_contrast.setValue(0)
        self.slider_contrast.valueChanged.connect(self.adjust_contrast)
        layout.addWidget(QLabel("Contrasto"))
        layout.addWidget(self.slider_contrast)

        # Visualizzazione dell'immagine
        self.graphics_view = QGraphicsView()
        layout.addWidget(self.graphics_view)
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        self.graphics_view.setMouseTracking(True)
        self.graphics_view.viewport().installEventFilter(self)

        # Pulsante di salvataggio
        self.btn_save = QPushButton("Salva Immagine")
        self.btn_save.clicked.connect(self.save_image)
        layout.addWidget(self.btn_save)

    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Carica Immagine", DESKTOP_DIR, 
                                              "Immagini (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.svg)")
        if path:
            pm = QPixmap(path)
            if pm.isNull():
                QMessageBox.warning(self, "Errore", "Immagine non valida.")
                return
            self.original_pixmap = QPixmap(pm)  # Salviamo una copia per l'undo
            self.current_pixmap = pm
            self.show_pixmap(pm)
            # Resetta slider di luminosità e contrasto
            self.slider_brightness.setValue(0)
            self.slider_contrast.setValue(0)

    def show_pixmap(self, pm):
        self.scene.clear()
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

    def adjust_brightness(self, value):
        if not self.original_pixmap:
            return
        # Applica una semplice regolazione di luminosità
        image = self.original_pixmap.toImage()
        for y in range(image.height()):
            for x in range(image.width()):
                color = image.pixelColor(x, y)
                r = max(0, min(255, color.red() + value))
                g = max(0, min(255, color.green() + value))
                b = max(0, min(255, color.blue() + value))
                image.setPixelColor(x, y, QColor(r, g, b))
        self.current_pixmap = QPixmap.fromImage(image)
        self.show_pixmap(self.current_pixmap)

    def adjust_contrast(self, value):
        if not self.original_pixmap:
            return
        # Applica una regolazione di contrasto semplice
        factor = (259 * (value + 255)) / (255 * (259 - value))
        image = self.original_pixmap.toImage()
        for y in range(image.height()):
            for x in range(image.width()):
                color = image.pixelColor(x, y)
                r = max(0, min(255, factor * (color.red() - 128) + 128))
                g = max(0, min(255, factor * (color.green() - 128) + 128))
                b = max(0, min(255, factor * (color.blue() - 128) + 128))
                image.setPixelColor(x, y, QColor(r, g, b))
        self.current_pixmap = QPixmap.fromImage(image)
        self.show_pixmap(self.current_pixmap)

    def rotate_image(self, angle):
        if not self.current_pixmap:
            return
        transform = QTransform().rotate(angle)
        rotated = self.current_pixmap.transformed(transform, Qt.SmoothTransformation)
        self.current_pixmap = rotated
        self.show_pixmap(rotated)

    def undo(self):
        if self.original_pixmap:
            self.current_pixmap = QPixmap(self.original_pixmap)
            self.show_pixmap(self.current_pixmap)
            # Reset slider di luminosità e contrasto
            self.slider_brightness.setValue(0)
            self.slider_contrast.setValue(0)

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
        self.label_title.setText(lm.get_text(lang, "IMAGE_EDITOR", default="Modifica Immagine"))
        self.btn_load.setText(lm.get_text(lang, "LOAD_IMAGE", default="Carica Immagine"))
        self.btn_apply_effect.setText(lm.get_text(lang, "APPLY_EFFECT", default="B/N"))
        self.btn_crop.setText(lm.get_text(lang, "CROP_IMAGE", default="Ritaglia"))

# =========================================================
#   HistoryWidget
# =========================================================
class HistoryWidget(QWidget):
    def __init__(self, username):
        super().__init__()
        self.username = username  # <--- per caricare la cronologia utente-specifica
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.label_title = QLabel("Cronologia Conversioni")
        self.label_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.label_title)
        
        self.list_history = QListWidget()
        layout.addWidget(self.list_history)
        
        # Pulsante per aggiornare la cronologia
        self.btn_refresh = QPushButton("Aggiorna")
        self.btn_refresh.clicked.connect(self.load_history)
        layout.addWidget(self.btn_refresh)
        
        self.load_history()
        
        self.list_history.itemDoubleClicked.connect(self.open_converted_file)
    
    def load_history(self):
        self.list_history.clear()
        # Usa il file di cronologia personale
        history_file = f"history_{self.username}.json"
        if not os.path.exists(history_file):
            return
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for record in data:
                ts = record["timestamp"]
                inp = record["input"]
                outp = record["output"]
                item_text = f"[{ts}] {os.path.basename(inp)} -> {os.path.basename(outp)}"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.UserRole, record)
                self.list_history.addItem(list_item)
        except Exception as e:
            print("Errore caricamento cronologia:", e)
    
    def open_converted_file(self, item):
        record = item.data(Qt.UserRole)
        out_path = record["output"]
        if os.path.exists(out_path):
            import webbrowser
            webbrowser.open(out_path)
        else:
            QMessageBox.warning(self, "File non trovato", f"Il file {out_path} non esiste.")
    
    def update_language(self, lang, lm):
        self.label_title.setText(lm.get_text(lang, "HISTORY_TITLE", default="Cronologia Conversioni"))
        self.btn_refresh.setText(lm.get_text(lang, "REFRESH_HISTORY", default="Aggiorna"))

# =========================================================
#   SingleConversionWidget (modificato per gestire più file, cartelle e zip)
# =========================================================
class SingleConversionWidget(QWidget):

    updateProgress = pyqtSignal(int)
    updateStatus = pyqtSignal(str)
    showError = pyqtSignal(str)
    setProgressVisible = pyqtSignal(bool)
    resetFieldsSignal = pyqtSignal()

    def __init__(self, advanced_options, username):
        super().__init__()
        self.advanced_options = advanced_options
        self.username = username  # <--- usato per log_conversion
        self.selected_files = []  # <--- lista di file/cartelle selezionati
        self.last_output_file = None
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.label_info = QLabel("Trascina qui i file oppure clicca 'Aggiungi File'")
        self.label_info.setStyleSheet("border: 2px dashed #aaa; padding: 30px; color: #000;")
        self.label_info.setAlignment(Qt.AlignCenter)
        self.label_info.setWordWrap(True)
        layout.addWidget(self.label_info)
        
        self.setAcceptDrops(True)
        
        # Lista di file (multi-selezione)
        self.list_files = FileListWidget(self)
        layout.addWidget(self.list_files)
        
        self.btn_select = QPushButton("Aggiungi File")
        self.btn_select.setStyleSheet("color: #000;")
        self.btn_select.clicked.connect(self.select_files)
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

         # Colleghiamo i segnali alle slot appropriate (che vengono eseguite nel thread principale)
        self.updateProgress.connect(self.progress_bar.setValue)
        self.updateStatus.connect(self.label_status.setText)
        self.showError.connect(lambda msg: QMessageBox.critical(self, "Errore Conversione", msg))
        self.resetFieldsSignal.connect(self.reset_fields)

    # Metodo per rimuovere gli elementi selezionati dalla lista
    def remove_selected_files(self):
        # Ottieni gli elementi selezionati e i loro indici
        selected_items = self.list_files.selectedItems()
        selected_rows = [self.list_files.row(item) for item in selected_items]
        # Rimuovi gli elementi partendo dall'indice più alto per non alterare gli indici
        for row in sorted(selected_rows, reverse=True):
            self.list_files.takeItem(row)
            del self.selected_files[row]

    # Metodo per resettare i campi (svuotare la lista, il combobox e ripristinare il messaggio)
    def reset_fields(self):
        self.selected_files.clear()
        self.list_files.clear()
        self.combo_format.clear()
        self.label_info.setText("Trascina qui i file oppure clicca 'Aggiungi File'")
    

    def open_advanced_dialog(self):
        dialog = ConversionOptionsDialog(self.advanced_options)
        dialog.exec_()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                path = url.toLocalFile()
                self.selected_files.append(path)
                self.list_files.addItem(path)
            event.acceptProposedAction()
            self.update_formats()
    
    def select_files(self):
        # Permetti selezione multipla
        files, _ = QFileDialog.getOpenFileNames(self, "Seleziona File", DESKTOP_DIR, "All Files (*.*)")
        if files:
            for path in files:
                self.selected_files.append(path)
                self.list_files.addItem(path)
            self.update_formats()

    def update_formats(self):
        """
        Determina i formati di uscita possibili a seconda del tipo di file (o files) selezionati.
        - Se c'è solo 1 cartella: abilitiamo solo la compressione (.zip).
        - Se c'è solo 1 file .zip: abilitiamo solo .unzipped.
        - Se ci sono più file, controlliamo se hanno la stessa estensione e mostriamo i formati possibili.
        - Se c'è un mix di estensioni diverse => "Formato non supportato".
        """
        self.combo_format.clear()
        
        if not self.selected_files:
            return
        
        # Selezioni speciali: cartella singola o zip singolo
        if len(self.selected_files) == 1:
            single_path = self.selected_files[0]
            if os.path.isdir(single_path):
                # Cartella -> comprimi
                self.combo_format.addItem(".zip")
                self.btn_convert.setText("Comprimi")
                return
            else:
                ext = os.path.splitext(single_path)[1].lower()
                if ext == ".zip":
                    self.combo_format.addItem(".unzipped")
                    self.btn_convert.setText("Decomprimi")
                    return
        
        # Altrimenti, per più file o file singolo “normale”, verifichiamo se tutti hanno la stessa estensione
        exts = []
        folders_count = 0
        zip_count = 0
        
        for f in self.selected_files:
            if os.path.isdir(f):
                folders_count += 1
            else:
                e = os.path.splitext(f)[1].lower()
                if e == ".zip":
                    zip_count += 1
                exts.append(e)
        
        # Se ci sono cartelle mescolate a file normali => non gestito
        if folders_count > 0 or zip_count > 0:
            # Non gestiamo scenario "misto" (cartelle + file)
            self.combo_format.addItem("Formato non supportato")
            self.btn_convert.setText("Converti")
            return
        
        # Se c'è almeno un file, controlla che tutte le estensioni siano uguali
        unique_exts = set(exts)
        if len(unique_exts) != 1:
            # estensioni diverse => errore
            self.combo_format.addItem("Formato non supportato")
            self.btn_convert.setText("Converti")
            return
        
        # Ok, c'è una sola estensione
        ext_in = unique_exts.pop()
        self.btn_convert.setText("Converti")  # di default
        formats = []

        if ext_in == ".docx":
            formats = [".pdf", ".pages", ".txt"]
        elif ext_in == ".pdf":
            formats = [".docx", ".pages", ".txt"]
        elif ext_in in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg"]:
            # Esempio di formati immagine
            formats = [".jpg", ".png", ".pdf", ".webp"]
        else:
            # Formato sconosciuto
            self.combo_format.addItem("Formato non supportato")
            return
        
        for f in formats:
            self.combo_format.addItem(f)

    def do_conversion(self):
        if not self.selected_files:
            QMessageBox.warning(self, "Attenzione", "Nessun file selezionato!")
            return
        
        out_ext = self.combo_format.currentText()
        if out_ext == "Formato non supportato":
            QMessageBox.warning(self, "Attenzione", "Formato non supportato!")
            return
        
        # Riconfigura il pulsante in base a cartella singola o zip singolo
        if len(self.selected_files) == 1:
            single_path = self.selected_files[0]
            if os.path.isdir(single_path):
                # Cartella => comprimi
                self.compress_folder(single_path)
                return
            else:
                ext = os.path.splitext(single_path)[1].lower()
                if ext == ".zip" and out_ext == ".unzipped":
                    # Decomprimi
                    self.decompress_zip(single_path)
                    return
        
        # Se qui, allora conversione multipla di file singoli (tutti stessa estensione)
        def conversion_worker():
            try:
                # Invia segnale per rendere visibile la progress bar e inizializzarla a 0
                self.setProgressVisible.emit(True)
                self.updateProgress.emit(0)
                chunk = 100 // max(1, len(self.selected_files))
                current_progress = 0

                for idx, in_path in enumerate(self.selected_files):
                    base, _ = os.path.splitext(in_path)
                    out_path = base + out_ext

                    self.convert_single_file(in_path, out_path)
                    
                    log_conversion(self.username, in_path, out_path)
                    
                    current_progress += chunk
                    self.updateProgress.emit(current_progress)
                    self.last_output_file = out_path

                self.updateProgress.emit(100)
                time.sleep(0.3)
                self.setProgressVisible.emit(False)
                self.updateStatus.emit(f"Convertito in: {out_ext}")
                self.resetFieldsSignal.emit()
            except Exception as e:
                self.setProgressVisible.emit(False)
                self.showError.emit(str(e))
        
        threading.Thread(target=conversion_worker).start()
    
    def convert_single_file(self, in_path, out_path):
        """
        Esegue la conversione effettiva per un singolo file (docx, pdf, immagine).
        """
        ext_in = os.path.splitext(in_path)[1].lower()
        ext_out = os.path.splitext(out_path)[1].lower()

        # Se l'input è un file ZIP e l'utente ha scelto di decomprimerlo (in teoria gestito sopra)
        if ext_in == ".zip" and ext_out == ".unzipped":
            decompress_zip(in_path)
            return
        
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
            # Altrimenti tentiamo la conversione immagine
            convert_image(in_path, out_path)
    
    def compress_folder(self, folder_path):
        def worker():
            try:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                zip_path = os.path.splitext(folder_path)[0] + ".zip"
                archive_path = compress_folder(folder_path, zip_path)
                time.sleep(1)
                self.progress_bar.setValue(100)
                self.progress_bar.setVisible(False)
                self.label_status.setText(f"Cartella compressa in: {archive_path}")
                self.last_output_file = archive_path
                log_conversion(self.username, folder_path, archive_path)
            except Exception as e:
                self.progress_bar.setVisible(False)
                QMessageBox.critical(self, "Errore Compressione", str(e))

        t = threading.Thread(target=worker)
        t.start()

    def decompress_zip(self, zip_path):
        def worker():
            try:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                out_folder = os.path.splitext(zip_path)[0] + "_unzipped"
                decompress_zip(zip_path, out_folder)
                time.sleep(1)
                self.progress_bar.setValue(100)
                self.progress_bar.setVisible(False)
                self.label_status.setText(f"Archivio decompresso in: {out_folder}")
                self.last_output_file = out_folder
                log_conversion(self.username, zip_path, out_folder)
            except Exception as e:
                self.progress_bar.setVisible(False)
                QMessageBox.critical(self, "Errore Decompressione", str(e))
        
        t = threading.Thread(target=worker)
        t.start()
    
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
        self.label_info.setText(lm.get_text(lang, "SINGLE_INFO", default="Trascina qui i file oppure clicca 'Aggiungi File'"))
        self.btn_select.setText(lm.get_text(lang, "SELECT_FILE", default="Aggiungi File"))
        self.btn_advanced.setText(lm.get_text(lang, "ADVANCED_OPTIONS", default="Opzioni Avanzate"))
        # Il testo del pulsante "Converti" può variare in base al contenuto (cartella/zip).
        # Ma qui di default forziamo "Converti". Poi in update_formats lo cambiamo dinamicamente.
        self.btn_convert.setText(lm.get_text(lang, "CONVERT_BUTTON", default="Converti"))
        self.btn_upload_drive.setText(lm.get_text(lang, "UPLOAD_DRIVE", default="Carica su Drive"))

# =========================================================
#   MergePDFWidget
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
        files, _ = QFileDialog.getOpenFileNames(self, "Seleziona PDF", DESKTOP_DIR, "PDF Files (*.pdf)")
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
        from conversions import merge_pdfs
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
        self.label_info.setText(lm.get_text(lang, "MERGE_INFO", default="Trascina qui i file PDF da unire oppure usa 'Aggiungi PDF'"))
        self.btn_add.setText(lm.get_text(lang, "ADD_PDF", default="Aggiungi PDF"))
        self.btn_up.setText(lm.get_text(lang, "MOVE_UP", default="Su"))
        self.btn_down.setText(lm.get_text(lang, "MOVE_DOWN", default="Giù"))
        self.btn_merge.setText(lm.get_text(lang, "MERGE_BUTTON", default="Unisci PDF"))

# =========================================================
#   SplitPDFWidget
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
        path, _ = QFileDialog.getOpenFileName(self, "Seleziona PDF", DESKTOP_DIR, "PDF Files (*.pdf)")
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
        self.label_info.setText(lm.get_text(lang, "SPLIT_INFO", default="Trascina qui un PDF oppure usa 'Seleziona PDF'"))
        self.btn_select.setText(lm.get_text(lang, "SELECT_PDF", default="Seleziona PDF"))
        self.line_pages.setPlaceholderText(lm.get_text(lang, "EXTRACT_PAGES", default="Estrai Pagine"))
        self.btn_split.setText(lm.get_text(lang, "EXTRACT_PAGES", default="Estrai Pagine"))

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
        settings = QSettings("MyCompany", "ConverterApp")
        self.current_lang = settings.value(f"{self.username}_language", "it")
        self.setWindowTitle("Universal Converter - Navigation Menu")
        self.setMinimumSize(1000, 600)
        
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

        # Nel costruttore della MainWindow, subito dopo aver creato la toolbar:
        self.btn_help = QPushButton("?")
        self.btn_help.setToolTip("Aiuto")
        self.btn_help.clicked.connect(self.show_help)
        self.toolbar.addWidget(self.btn_help)

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

        self.btn_history = QPushButton()
        self.btn_history.setObjectName("menuButton")
        self.btn_history.clicked.connect(lambda: self.switch_page(4))
        nav_layout.addWidget(self.btn_history)
        
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
        
        # Inizializziamo le pagine passando username dove serve
        self.page_single = SingleConversionWidget(self.advanced_options, self.username)
        self.page_merge = MergePDFWidget()
        self.page_split = SplitPDFWidget()
        self.page_image_editor = ImageEditorWidget()
        self.page_history = HistoryWidget(self.username)  # <--- passiamo username
        
        self.stack.addWidget(self.page_single)       # indice 0
        self.stack.addWidget(self.page_merge)        # indice 1
        self.stack.addWidget(self.page_split)        # indice 2
        self.stack.addWidget(self.page_image_editor) # indice 3
        self.stack.addWidget(self.page_history)      # indice 4
        
        main_layout.addWidget(self.nav_panel)
        main_layout.addWidget(self.stack)

                # All'interno del costruttore di MainWindow, dopo aver creato self.stack e le pagine:
        self.shortcut_single = QShortcut(QKeySequence("Meta+1"), self)
        self.shortcut_single.setContext(Qt.ApplicationShortcut)
        self.shortcut_single.activated.connect(lambda: self.switch_page(0))

        self.shortcut_merge = QShortcut(QKeySequence("Meta+2"), self)
        self.shortcut_merge.setContext(Qt.ApplicationShortcut)
        self.shortcut_merge.activated.connect(lambda: self.switch_page(1))

        self.shortcut_split = QShortcut(QKeySequence("Meta+3"), self)
        self.shortcut_split.setContext(Qt.ApplicationShortcut)
        self.shortcut_split.activated.connect(lambda: self.switch_page(2))

        self.shortcut_image = QShortcut(QKeySequence("Meta+4"), self)
        self.shortcut_image.setContext(Qt.ApplicationShortcut)
        self.shortcut_image.activated.connect(lambda: self.switch_page(3))

        self.shortcut_history = QShortcut(QKeySequence("Meta+5"), self)
        self.shortcut_history.setContext(Qt.ApplicationShortcut)
        self.shortcut_history.activated.connect(lambda: self.switch_page(4))


        
        self.apply_theme()
        self.apply_language()
        self.update_menu_styles()


    def show_help(self):
            help_dialog = HelpDialog(self)
            help_dialog.exec_()

    # --------------------------------------------------------
    # SEZIONE: Metodi di login persistente
    # --------------------------------------------------------
    def do_logout(self):
        # Cancella il login persistente
        clear_login()
        self.close()

        login = LoginDialog()
        if login.exec_() == QDialog.Accepted:
            # Se l'utente fa di nuovo login
            save_login(login.logged_username)
            new_main = MainWindow(login.logged_username, login.logged_password)
            new_main.show()

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
        buttons = [self.btn_single, self.btn_merge, self.btn_split, self.btn_image_editor, self.btn_history]
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
            # Salva la lingua per l'utente corrente
            settings = QSettings("MyCompany", "ConverterApp")
            settings.setValue(f"{self.username}_language", self.current_lang)
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
                QPushButton:hover {
                    background-color: #e6f0ff;
                }
                QPushButton:hover#menuButton { 
                    background-color: #007BFF;
                    color: white;
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
                QPushButton:hover {
                    background-color: #444444;
                }
                QPushButton:hover#menuButton { 
                    background-color: #ff8c00; 
                    color: black;
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
        
        self.btn_single.setText(lm.get_text(lang, "MENU_SINGLE", default="Singola Conversione"))
        self.btn_merge.setText(lm.get_text(lang, "MENU_MERGE", default="Unisci PDF"))
        self.btn_split.setText(lm.get_text(lang, "MENU_SPLIT", default="Estrai Pagine PDF"))
        self.btn_image_editor.setText(lm.get_text(lang, "IMAGE_EDITOR", default="Modifica Immagine"))
        self.btn_options.setText(lm.get_text(lang, "OPTIONS", default="Opzioni"))
        self.btn_logout.setText(lm.get_text(lang, "LOGOUT", default="Esci"))
        self.btn_history.setText(lm.get_text(lang, "MENU_HISTORY", default="Cronologia"))
        self.label_user_icon.setText("👤")
        self.label_user_name.setText(self.username)
        
        # Aggiorniamo i widget interni, se supportano update_language
        if hasattr(self.page_single, "update_language"):
            self.page_single.update_language(lang, lm)
        if hasattr(self.page_merge, "update_language"):
            self.page_merge.update_language(lang, lm)
        if hasattr(self.page_split, "update_language"):
            self.page_split.update_language(lang, lm)
        if hasattr(self.page_image_editor, "update_language"):
            self.page_image_editor.update_language(lang, lm)
        if hasattr(self.page_history, "update_language"):
            self.page_history.update_language(lang, lm)
