from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget
from PySide2.QtGui import QPalette, QImage, QBrush


class BackgroundedWidget(QWidget):
    def __init__(self, paret):
        super(BackgroundedWidget, self).__init__()
        # NB! Без установки setAutoFillBackground не работает
        self.setAutoFillBackground(True)

    def resizeEvent(self, event):
        palette = QPalette()
        img = QImage("../img/background.png")
        # Если нужно сохранять пропорции, то вместо IgnoreAspectRatio использовать KeepAspectRatioByExpanding
        scaled = img.scaled(self.size(), Qt.IgnoreAspectRatio, transformMode=Qt.SmoothTransformation)
        palette.setBrush(QPalette.Window, QBrush(scaled))
        self.setPalette(palette)
