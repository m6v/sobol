from PySide2 import QtCore, QtWidgets

from UiLoader import UiLoader
from SobolDialog import SobolDialog

board_init_message = """
Вы переходите в режим инициализации платы.
В результате инициализации текущие
настройки будут обновлены,
пользователи удалены и администратор
будет зарегистрирован заново.
Продолжить?
"""

id_format_message = """
В результате форматирования на
идентификаторе будут уничтожены все
данные.
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
        self.id_format_push_button.clicked.connect(self.id_format)

    def send_board_init_request(self):
        """Показать диалог с подтверждением программной инициализации платы"""
        dialog = SobolDialog("Внимание", board_init_message, QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.No)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.boardInitRequested.emit()

    def id_format(self):
        dialog = SobolDialog("Внимание", id_format_message, QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.No)
        dialog.exec_()
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # TODO Уточнить, что болжно быть при подтверждении форматирования
            pass
