#!/usr/bin/env python3
__author__ = 'Sergey Maksimov'
__mail__ = 'm6v@mail.ru'
__version__ = '0.2'
__date__ = '2025-10-03'
__copyright__ = 'Copyright © 2025 Sergey Maksimov'
__licence__ = 'GNU Public Licence (GPL) v3'

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

import functools
import sys
from PyQt5 import QtWidgets
from PyQt5.Qt import QApplication, QIcon, QAction

DBusGMainLoop(set_as_default=True)


class MyService(dbus.service.Object):
    def __init__(self, bus_name, object_path):
        dbus.service.Object.__init__(self, bus_name, object_path)

    @dbus.service.signal('com.example.MyInterface', signature='s')
    def MySignal(self, message):
        """Emits a signal with a string message."""
        print(f"Emitting MySignal with message: {message}")

    @dbus.service.method('com.example.MyInterface', in_signature='s', out_signature='s')
    def SayHello(self, name):
        print(f"Received SayHello call from {name}")
        return f"Hello, {name}!"


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Установить соединение с сессионной шиной D-Bus
    # для системной шины использовать dbus.SystemBus()
    bus = dbus.SessionBus()
    bus_name = dbus.service.BusName('com.example.MyService', bus)
    service_object = MyService(bus_name, '/com/example/MyService')

    tray_icon = QtWidgets.QSystemTrayIcon()
    tray_icon.setIcon(QIcon("icons/ibutton.png"))
    tray_icon.show()

    def ibutton_action_triggered(index):
        print(index)
        # Вызвать метод
        # reply = bus_interface.SayHello()
        # reply = bus_interface.StringEcho(index)
        # print(reply)
        # Отправить сигнал
        service_object.MySignal("This is a broadcast message with id: %i" % index)

    tray_menu = QtWidgets.QMenu()
    actions = []
    for i in range(10):
        action = QAction("iButton: #%s" % i)
        action.triggered.connect(functools.partial(ibutton_action_triggered, i))
        tray_menu.addAction(action)
        actions.append(action)

    tray_icon.setContextMenu(tray_menu)

    sys.exit(app.exec())

    '''
    # Так как используется основной цикл класса QApplication,
    # то дальнейший код не нужен (оставлен для примера)
    loop = GLib.MainLoop()
    
    # Run the GLib main loop to keep the service alive and handle D-Bus events
    print("Service running, press Ctrl+C to exit.")
    try:
        loop.run()
    except KeyboardInterrupt:
        print("Exiting main loop.")
        loop.quit()
    '''
