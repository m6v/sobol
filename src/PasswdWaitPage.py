import logging

from PySide2.QtCore import Qt
from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QPalette, QImage, QBrush

from UiLoader import UiLoader


class PasswdWaitPage(QtWidgets.QWidget):
    """Страница ожидания ввода пароля"""
    passwdEntered = QtCore.Signal(str)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/PasswdWaitPage.ui", self)

        self.setStyleSheet("""
            QPushButton { border: 2px solid white; color: white; }
            QLabel { color: white; }
            """)

        self.enter_push_button.clicked.connect(self.person_auth)

    def person_auth(self):
        """Аутентифицировать пользователя(администратора) и отправить сигнал"""
        passwd = self.passwd_line_edit.text()
        if passwd:
            self.passwdEntered.emit(passwd)

    def resizeEvent(self, event):
        palette = QPalette()
        img = QImage("../img/background.png")
        # Если нужно сохранять пропорции, то вместо IgnoreAspectRatio
        # использовать KeepAspectRatioByExpanding
        scaled = img.scaled(self.size(), Qt.IgnoreAspectRatio)
        palette.setBrush(QPalette.Window, QBrush(scaled))
        self.setPalette(palette)
