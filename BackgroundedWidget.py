from PyQt5.Qt import QWidget, QPalette, QImage, QBrush, QColor
from PyQt5.QtCore import Qt

class BackgroundedWidget(QWidget):
    def __init__(self):
       super(QWidget, self).__init__()
       # Без установки setAutoFillBackground не работает!
       self.setAutoFillBackground(True)

    def resizeEvent(self, event):
        palette = QPalette()
        img = QImage("background.png")
        # Если нужно сохранять пропорции, то вместо IgnoreAspectRatio использовать KeepAspectRatioByExpanding
        scaled = img.scaled(self.size(), Qt.IgnoreAspectRatio, transformMode = Qt.SmoothTransformation)
        palette.setBrush(QPalette.Window, QBrush(scaled))
        self.setPalette(palette)
