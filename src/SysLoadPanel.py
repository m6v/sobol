import functools
import json
import logging
import subprocess

from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QShowEvent

from Toggle import Toggle
from UiLoader import UiLoader
from WidgetStateManager import WidgetStateManager


class SysLoadPanel(QtWidgets.QWidget):
    sys_load_requested = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Создается дважды при создании BoardInitPage и BoardSettingsPage

        self.loader = UiLoader()
        # Загружаем интерфейс и регистрируем кастомный класс Toggle
        self.loader.loadUi("../ui/SysLoadPanel.ui", self, Toggle)

        self.setObjectName("sysload_panel")
        self.widget_state_manager = WidgetStateManager()

        self.sys_load_push_button.clicked.connect(self.sys_load_requested.emit)
        self.save_push_button.clicked.connect(functools.partial(self.widget_state_manager.save_state, self))

        try:
            # Получить имя диска на который смотирован корень
            cmd = "df / --output=source | tail -1 | xargs lsblk -no pkname"
            disk_name = subprocess.check_output(cmd, shell=True, text=True).strip()
            # Получить имя, модель, серийный новер, порт подключения и размер накопителей
            cmd = f"lsblk -J -d -o NAME,MODEL,SERIAL,TRAN,SIZE /dev/{disk_name}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout).get("blockdevices", {})[0]
            # Заменить отсутствующие значения на N/A
            disk_info = {key: (value if value is not None else "N/A") for key, value in data.items()}
            logging.debug(disk_info)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logging.error(e)

        self.disk_model_value.setText(disk_info["model"])
        self.serial_ctl_value.setText(disk_info["serial"])
        self.port_ctl_value.setText(disk_info["tran"])

    def showEvent(self, event: QShowEvent):
        """Используем обработчик события отображения виджета, чтобы восстановить его настройки.
        Это необходимо выполнять каждый раз, чтобы без нажатия кнопки [Сохранить],
        после переключения панелей восстанавливались несохраненные настройки"""
        self.widget_state_manager.load_state(self)
        # Обязательно вызываем базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
