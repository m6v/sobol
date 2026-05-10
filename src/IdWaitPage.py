from PySide2.QtCore import Qt
from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QPalette, QImage, QBrush

from UiLoader import UiLoader


class IdWaitPage(QtWidgets.QWidget):
    """Страница ожидания предъявления ibutton"""
    ibuttonPresented = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/IdWaitPage.ui", self)

        self.setStyleSheet("""
            QPushButton { border: 2px solid white; color: white; }
            QLabel { color: white; }
            """)

    def resizeEvent(self, event):
        palette = QPalette()
        img = QImage("../img/background.png")
        # Если нужно сохранять пропорции, то вместо IgnoreAspectRatio
        # использовать KeepAspectRatioByExpanding
        scaled = img.scaled(self.size(), Qt.IgnoreAspectRatio)
        palette.setBrush(QPalette.Window, QBrush(scaled))
        self.setPalette(palette)

    def on_ibutton_presented(self, message):
        """Ретранслироввать полученный сигнал"""
        self.ibuttonPresented.emit()
