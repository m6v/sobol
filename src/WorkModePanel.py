from PySide2 import QtWidgets

from Toggle import Toggle
from UiLoader import UiLoader


class WorkModePanel(QtWidgets.QWidget):
    """Панель изменения режима работы"""
    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        # Загружаем интерфейс и регистрируем кастомный класс Toggle
        self.loader.loadUi("../ui/WorkModePanel.ui", self, Toggle)
