#!/usr/bin/env python3
__author__ = 'Sergey Maksimov'
__mail__ = 'm6v@mail.ru'
__version__ = '0.2'
__date__ = '2025-10-03'
__copyright__ = 'Copyright © 2025 Sergey Maksimov'
__licence__ = 'GNU Public Licence (GPL) v3'

import functools
import logging
import json
import os
import signal
import sys

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

from PyQt5 import QtWidgets
from PyQt5.Qt import QApplication, QIcon, QAction

DBusGMainLoop(set_as_default=True)

# Получить имя скрипта без расширения
appname = os.path.splitext(os.path.basename(__file__))[0]
logfile = appname + ".log"

# Если требуется логирование в файл добавить аргумент filename=logfile
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logging.info("%s started" % appname)

with open("ibuttons.json") as file:
    ibuttons = json.load(file)


class IButtonService(dbus.service.Object):
    def __init__(self, bus_name, object_path):
        dbus.service.Object.__init__(self, bus_name, object_path)

    @dbus.service.signal("com.example.IButtonInterface", signature="a{sv}")
    def IButtonSignal(self, message):
        """Отправить сигнал, содержащий словарь"""
        logging.info(f"Emitting IButtonSignal with message: {message}")

    @dbus.service.method("com.example.IButtonInterface", in_signature="a{sv}", out_signature="b")
    def SetIButtonData(self, data):
        """Записать данные в ibutton"""
        logging.info(f"Calling SetIButtonData method with data: {data}")
        ibuttons[str(data["id"])] = {"user_name": str(data["user_name"]), "passwd": str(data["passwd"])}
        logging.info(f"IButtons is {ibuttons}")
        # Записать измененный словарь ibuttons в файл
        with open("ibuttons.json", "w") as file:
            json.dump(ibuttons, file, ensure_ascii=False)
        return True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Явная обработка сигнала SIGINT с подключением его к механизму завершения работы приложения,
    # иначе из консоли не завершить приложение нажатием Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Установить соединение с сессионной шиной D-Bus
    bus = dbus.SessionBus()
    bus_name = dbus.service.BusName("com.example.IButtonService", bus)
    service_object = IButtonService(bus_name, "/com/example/IButtonService")

    tray_icon = QtWidgets.QSystemTrayIcon()
    tray_icon.setIcon(QIcon("icons/ibutton.png"))
    tray_icon.show()

    def ibutton_action_triggered(item):
        """Отправить сигнал, содержащий словарь item"""
        logging.info(f"Reading iButton: {item}")
        message = dict(ibuttons[item], id=item)
        service_object.IButtonSignal(message)

    tray_menu = QtWidgets.QMenu()
    actions = []
    for item in ibuttons:
        action = QAction(item)
        action.triggered.connect(functools.partial(ibutton_action_triggered, item))
        tray_menu.addAction(action)
        actions.append(action)

    tray_icon.setContextMenu(tray_menu)

    sys.exit(app.exec())
