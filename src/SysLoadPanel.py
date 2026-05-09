import functools

from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QShowEvent

from Toggle import Toggle
from UiLoader import UiLoader
from WidgetStateManager import WidgetStateManager


class SysLoadPanel(QtWidgets.QWidget):
    sys_load_requested = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        # Загружаем интерфейс и регистрируем кастомный класс Toggle
        self.loader.loadUi("../ui/SysLoadPanel.ui", self, Toggle)

        self.setObjectName("sysload_panel")
        self.widget_state_manager = WidgetStateManager()

        self.sys_load_push_button.clicked.connect(self.sys_load_requested.emit)
        self.save_push_button.clicked.connect(functools.partial(self.widget_state_manager.save_state, self))

    def showEvent(self, event: QShowEvent):
        """Используем обработчик события отображения виджета, чтобы восстановить его настройки.
        Это необходимо выполнять каждый раз, чтобы без нажатия кнопки [Сохранить],
        после переключения панелей восстанавливались несохраненные настройки"""
        self.widget_state_manager.load_state(self)
        # Обязательно вызываем базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
