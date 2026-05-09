import functools
import logging

from PySide2.QtCore import Qt
from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QPalette, QImage, QBrush

from UiLoader import UiLoader


class UserChoicePage(QtWidgets.QWidget):
    """Страница настроек"""
    sys_load_requested = QtCore.Signal()
    user_passwd_change_requested = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/UserChoicePage.ui", self)

        self.setStyleSheet("""
            QPushButton { border: 2px solid white; color: white; }
            QLabel { color: white; }
            """)

        self.sys_load_push_button.clicked.connect(self.sys_load_requested.emit)
        self.change_passwd_push_button.clicked.connect(self.user_passwd_change_requested.emit)

    def resizeEvent(self, event):
        palette = QPalette()
        img = QImage("../img/background.png")
        # Если нужно сохранять пропорции, то вместо IgnoreAspectRatio
        # использовать KeepAspectRatioByExpanding
        scaled = img.scaled(self.size(), Qt.IgnoreAspectRatio)
        palette.setBrush(QPalette.Window, QBrush(scaled))
        self.setPalette(palette)

    def on_ibutton_present(self, message):
        logging.debug(message)

