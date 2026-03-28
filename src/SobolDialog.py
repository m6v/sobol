import logging

from PySide2 import QtCore, QtWidgets
from UiLoader import UiLoader


class SobolDialog(QtWidgets.QDialog):
    """Выводит кастомизированное диалоговое окно"""
    def __init__(self, title, text, buttons=None, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("SobolDialog.ui", self)

        self.setWindowTitle(title)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        # Если кнопки не переданы, отображать только [OK]
        if buttons is None:
            buttons = QtWidgets.QDialogButtonBox.Ok
        self.button_box = QtWidgets.QDialogButtonBox(buttons)

        self.right_vertical_layout.addWidget(self.button_box)

        # Стандартные сигналы
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # Перехват нажатий всех кнопок
        self.button_box.clicked.connect(self.on_button_clicked)

        dialog_style_sheet = """
            QWidget {
                font: 9pt "Monospace Regular";
                background-color: #F5F5F5;
            }
            QPushButton {
                background-color: #48A23F;
                width: 120px;
                height: 48px;
                color: white;
           }
           QPushButton:hover {
                background: #3D8A36;
           }
           QPushButton:pressed {
                background-color: #3D8A36;
           }
        """
        self.setStyleSheet(dialog_style_sheet)
        self.caption_label.setText(title)
        self.text_label.setText(text)

    def on_button_clicked(self, button):
        role = self.button_box.buttonRole(button)
        text = button.text()
        logging.debug(f"Button: {text}, role: {role} is clicked")

    def _center(self):
        """Центрировать окно диалога"""
        parent = self.parent()
        if parent:
            geometry = parent.geometry()
        else:
            geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
        # Двигает по разному в зависимости от наличия родителя и заголовка окна! Здесь не учтено!
        self.move((geometry.width() - self.width()) // 2, (geometry.height() - self.height()) // 2)

    def exec_(self):
        self._center()
        return super().exec_()
