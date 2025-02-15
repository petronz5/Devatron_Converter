import sys
from PyQt5.QtWidgets import QApplication, QDialog
from gui import MainWindow, LoginDialog

def main():
    app = QApplication(sys.argv)
    
    login = LoginDialog()
    if login.exec_() == QDialog.Accepted:
        window = MainWindow(login.logged_username, login.logged_password)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
