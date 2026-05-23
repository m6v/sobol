import functools
import json
import logging
import os
import subprocess

from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QShowEvent

from Toggle import Toggle
from UiLoader import UiLoader
from WidgetStateManager import WidgetStateManager


def get_boot_option() -> str:
    """Возвращает наименование текущей опции загрузки на основе данных ОС."""
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("NAME="):
                    return line.split("=")[1].strip().strip('"')
    except (FileNotFoundError, PermissionError):
        pass
    return "Linux-система"


def get_os_volume() -> str:
    """Определяет имя устройства корневого тома операционной системы."""
    try:
        root_dev = subprocess.check_output(
            ["findmnt", "-n", "-o", "SOURCE", "/"], 
            text=True, 
            stderr=subprocess.DEVNULL
        ).strip()
        if root_dev:
            return root_dev
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return "Не определено"


def get_os_loader() -> str:
    """Устанавливает путь к исполняемому файлу или тип загрузчика ОС."""
    # Стандартные пути верификации исполняемых файлов EFI
    efi_paths = [
        "/boot/efi/EFI/astra/grubx64.efi",
        "/boot/efi/EFI/ubuntu/grubx64.efi",
        "/boot/efi/EFI/redhat/grubx64.efi",
        "/boot/efi/EFI/altlinux/grubx64.efi",
        "/boot/efi/EFI/BOOT/BOOTX64.EFI"
    ]
    
    for path in efi_paths:
        try:
            if os.path.exists(path):
                return path
        except PermissionError:
            continue
            
    # Проверка структуры каталогов для Legacy/MBR конфигураций
    if os.path.exists("/boot/grub") or os.path.exists("/boot/grub2"):
        return "Встроенный загрузчик GRUB"
        
    return "Неизвестный загрузчик"


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

        self.load_option_value.setText(get_boot_option())
        self.sys_volume_value.setText(get_os_volume())
        self.sys_loader_value.setText(get_os_loader())

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
        # Вызвать базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
