import logging

from PySide2 import QtCore, QtWidgets

from UiLoader import UiLoader
from SobolDialog import SobolDialog

message = """
Вы переходите в режим инициализации платы.
В результате инициализации текущие
настройки будут обновлены,
пользователи удалены и администратор
будет зарегистрирован заново.
Продолжить?
"""

class ServiceOperationsPanel(QtWidgets.QWidget):
    boardInitRequested = QtCore.Signal()
    def __init__(self, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/ServiceOperationsPanel.ui", self)
        self.setObjectName("service_operations_panel")

        self.board_init_push_button.clicked.connect(self.send_board_init_request)

    def send_board_init_request(self):
        """Показать диалог с подтверждением программной инициализации платы"""
        dialog = SobolDialog("Внимание", message, QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.No)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.boardInitRequested.emit()
