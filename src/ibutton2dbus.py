#!/usr/bin/env python3
__author__ = 'Sergey Maksimov'
__mail__ = 'm6v@mail.ru'
__version__ = '1.3'
__date__ = '2026-05-14'
__copyright__ = 'Copyright © 2026 Sergey Maksimov'
__licence__ = 'GNU Public Licence (GPL) v3'
__description__ = 'Имитатор iButtons'

import functools
import logging
import json
import os
from pathlib import Path
import signal
import pwd
import shutil
import sys
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

from PySide2 import QtGui
from PySide2.QtWidgets import QApplication, QAction, QMenu, QSystemTrayIcon


# Путь к каталогу проекта и имя скрипта без расширения
basepath, appname = Path(__file__).resolve().parent.parents[0], Path(__file__).stem
# Логирование в файл logfile
logfile =  Path.home().joinpath(".cache", appname + ".log")
logging.basicConfig(level=logging.INFO, filename=logfile, format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

logging.info(f"{appname} started...")

class IButtonApp(dbus.service.Object):
    def __init__(self, bus_name, object_path):
        super().__init__(bus_name, object_path)
        self.config_file = Path.home().joinpath(".config", "sobol4emu", appname + ".json")
        if not self.config_file.is_file():
            # Если конфиг отсутствует, скопировать его шаблон
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(basepath.joinpath("ibuttons.json"), self.config_file)

        # Загрузить словарь ibuttons 
        self.ibuttons = self.load_data()

        # Создать меню в системном лотке
        self.tray_icon = QSystemTrayIcon(QtGui.QIcon(str(basepath.joinpath("img/ibutton.png"))))
        self.tray_menu = QMenu()

        # Создать элементы меню
        for item_id in self.ibuttons:
            action = QAction(str(item_id), self.tray_menu)
            action.triggered.connect(functools.partial(self.send_signal, item_id))
            self.tray_menu.addAction(action)

        self.tray_menu.addSeparator()
        exit_action = QAction("Выход", self.tray_menu)
        exit_action.triggered.connect(QApplication.instance().quit)
        self.tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        QApplication.instance().aboutToQuit.connect(self.cleanup)
        logging.info(f"{appname} initialized successfully")

    def load_data(self):
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load JSON config: {e}")
            return {}

    @dbus.service.signal("com.example.IButtonInterface", signature="a{sv}")
    def IButtonSignal(self, message):
        logging.info(f"D-Bus signal emitted: {message}")

    def send_signal(self, item_id):
        if item_id in self.ibuttons:
            message = dict(self.ibuttons[item_id], id=item_id)
            self.IButtonSignal(message)

    @dbus.service.method("com.example.IButtonInterface", in_signature="a{sv}", out_signature="b")
    def SetIButtonData(self, data):
        item_id = str(data.get("id"))
        if item_id in self.ibuttons:
            self.ibuttons[item_id] = {
                "user_name": str(data.get("user_name", "")),
                "passwd": str(data.get("passwd", ""))
            }
            try:
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.ibuttons, f, ensure_ascii=False, indent=4)
                logging.info(f"iButton data for '{item_id}' updated successfully")
                return True
            except IOError as e:
                logging.error(f"File write error: {e}")
        else:
            logging.warning(f"Update failed: ID '{item_id}' not found in configuration")
        return False

    def cleanup(self):
        logging.info(f"{appname} ended")


if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Явная обработка сигнала SIGINT с подключением его к механизму завершения работы приложения,
    # иначе из консоли не завершить приложение нажатием Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        bus = dbus.SessionBus()
        # Регистрация имени в шине
        name = dbus.service.BusName("ru.navis.ibutton2dbus", bus)
        # Создание объекта по пути
        service = IButtonApp(name, "/ru/navis/ibutton2dbus")
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical(f"D-Bus service startup failed: {e}")
