from PySide2 import QtCore, QtWidgets

from Toggle import Toggle
from UiLoader import UiLoader


class UsersListPanel(QtWidgets.QWidget):
    """Панель со списком и настройками учетных записей пользователей"""
    userRegistrationRequested = QtCore.Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        # Загружаем интерфейс и регистрируем кастомный класс Toggle
        self.loader.loadUi("../ui/UsersListPanel.ui", self, Toggle)

        self.add_user_push_button.clicked.connect(self.userRegistrationRequested.emit)
