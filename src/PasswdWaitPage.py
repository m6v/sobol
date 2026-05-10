from PySide2.QtCore import Qt
from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QPalette, QImage, QBrush, QShowEvent

from UiLoader import UiLoader


class PasswdWaitPage(QtWidgets.QWidget):
    """Страница ожидания ввода пароля"""
    passwdEntered = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAutoFillBackground(True)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/PasswdWaitPage.ui", self)

        self.setStyleSheet("""
            QPushButton { border: 2px solid white; color: white; }
            QLabel { color: white; }
            """)

        self.enter_push_button.clicked.connect(self.on_passwd_entered)
        self.passwd_line_edit.returnPressed.connect(self.on_passwd_entered)

    def on_passwd_entered(self):
        """Оправить сигнал, содержащий введенный пароль"""
        passwd = self.passwd_line_edit.text()
        if passwd:
            self.passwdEntered.emit(passwd)
        return

    def resizeEvent(self, event):
        palette = QPalette()
        img = QImage("../img/background.png")
        # Если нужно сохранять пропорции, то вместо IgnoreAspectRatio
        # использовать KeepAspectRatioByExpanding
        scaled = img.scaled(self.size(), Qt.IgnoreAspectRatio)
        palette.setBrush(QPalette.Window, QBrush(scaled))
        self.setPalette(palette)

    def showEvent(self, event: QShowEvent):
        """Стереть введенный во время предыдущей попытки аутентификации пароль"""
        self.passwd_line_edit.setText("")
        self.passwd_line_edit.setFocus()
        # Вызвать базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
