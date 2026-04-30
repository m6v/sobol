#!/usr/bin/env python3
import argparse
import configparser
import logging
import sys
from pathlib import Path

import dbus
import dbus.mainloop.glib

from PySide2 import QtCore, QtWidgets

from AdminChoicePage import AdminChoicePage
from BoardInitPage import BoardInitPage
from IdWaitPage import IdWaitPage
from BoardSettingsPage import BoardSettingsPage
from UserRegistrationPage import UserRegistrationPage


class MainWindow(QtWidgets.QMainWindow):
    # Сигнал "предъявления" iButton
    ibutton_present = QtCore.Signal(dict)

    def __init__(self, config):
        super().__init__()

        self.config = config

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.stack = QtWidgets.QStackedWidget()
        self.layout.addWidget(self.stack)

        self.board_init_page = BoardInitPage(config)

        self.id_wait_page = IdWaitPage(config)
        self.admin_choice_page = AdminChoicePage(config)
        self.board_settings_page = BoardSettingsPage(config)
        self.user_registration_page = UserRegistrationPage(config)

        self.id_wait_page.ibutton_presented.connect(lambda: self.set_page(self.admin_choice_page))
        self.admin_choice_page.sys_load_requested.connect(self.sys_load)
        self.admin_choice_page.show_settings_requested.connect(lambda: self.set_page(self.board_settings_page))
        self.board_settings_page.sys_load_panel.sys_load_requested.connect(self.sys_load)
        self.board_settings_page.users_list_panel.userRegistrationRequested.connect(lambda: self.set_page(self.user_registration_page))
        self.user_registration_page.registrationСompleted.connect(lambda: self.set_page (self.board_settings_page))

        self.stack.addWidget(self.board_init_page)
        self.stack.addWidget(self.id_wait_page)
        self.stack.addWidget(self.admin_choice_page)
        self.stack.addWidget(self.board_settings_page)
        self.stack.addWidget(self.user_registration_page)

        # TODO В зависимости от того инициализирован комплекс или нет,
        # показать страницу инициализации self.board_init_page или страницу ожидания iButton
        # self.set_page(self.id_wait_page)
        self.set_page(self.board_init_page)

        # Восстановление настроек окна
        try:
            self.setWindowTitle(self.config.get("window", "title", fallback='ПАК "Соболь"'))
            # Разбить строку на элементы, преобразовать их в целые числа и получить QRect с геометрией главного окна
            geometry = QtCore.QRect(*map(int, self.config.get("window", "geometry", fallback="0;0;1200;800").split(";")))
            # Восстановить геометрию и состояние главного окна
            self.setGeometry(geometry)
            state = int(self.config.get("window", "state", fallback="0"))
            self.restoreState(bytearray(state))
        except configparser.NoOptionError as e:
            logging.warning(e)
        except configparser.NoSectionError as e:
            logging.error(e)

        try:
            # Установить функцию обратного вызова для обработки сигнала IButtonSignal
            bus.add_signal_receiver(self.ibutton_signal_handler, bus_name='ru.navis.ibutton2dbus', signal_name="IButtonSignal")
            # Получить объект шины
            self.service_object = bus.get_object('ru.navis.ibutton2dbus', '/ru/navis/ibutton2dbus')
        except dbus.exceptions.DBusException as e:
            # Если имитатор считывателя iButton не запущен обработать исключения и завершить программу
            logging.error(e)
            sys.exit()

    def ibutton_signal_handler(self, message):
        """Функция обратного вызова для обработки сигнала с dBus"""
        logging.debug(f"Recieve message: {message}")
        # Запомнили последний предъявленный ibutton и оптравили сигнал
        self.message = message
        self.ibutton_present.emit(message)

    def set_page(self, widget):
        # Отключить сигнал у предыдущего виджета
        try:
            self.ibutton_present[dict].disconnect(self.stack.currentWidget().on_ibutton_presented)
        except (AttributeError, RuntimeError) as e:
            logging.debug(e)
        # Сделать текщим widget и установить сигнал
        self.stack.setCurrentWidget(widget)
        try:
            # Соединяем сигнал предъявления ibutton с методом нового виджета
            # Если обработчика нет, игнорируем исключение
            self.ibutton_present[dict].connect(widget.on_ibutton_presented)
        except AttributeError as e:
            logging.debug(e)

    def sys_load(self):
        self.close()

    def closeEvent(self, event):
        """Сохранить настройки приложения"""
        # Создать обязательные секции, если отсутствуют
        for section in ["window", "general"]:
            if not self.config.has_section(section):
                self.config.add_section(section)

        # Получить кортеж с элементами QRect геометрии главного окна
        geometry = self.geometry().getRect()
        # Преобразовать элементы кортежа в строки и разделить символом ;
        self.config.set("window", "geometry", ";".join(map(str, geometry)))
        self.config.set("window", "state", str(int(self.windowState())))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()

    parser = argparse.ArgumentParser(description='Эмулятор ПАК "Соболь"')
    parser.add_argument("config", nargs="?", help="Конфигурационный файл")
    args = parser.parse_args()

    # Если конфиг не задан, используем $HOME/.config/$program_name/default.conf
    program_name = Path(sys.argv[0]).stem
    if not args.config:
        config_path = Path.home().joinpath(".config", program_name, "default.conf")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.touch()
        logging.warning(f"Configuration file not specified, using '{config_path}'")
    else:
        config_path = Path(args.config)
        # Если путь к конфигу не задан (только имя),
        # ищем файл args.config в каталоге $HOME/.config/$program_name
        if len(config_path.parts) == 1:
            config_path = Path.home().joinpath(".config", program_name, args.config)

        if not config_path.exists():
            logging.error(f"Config {config_path} not found")
            sys.exit(1)

    config = configparser.ConfigParser(allow_no_value=True)
    # Установить чувствительность ключей к регистру
    config.optionxform = str
    config.read(config_path)

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(config)
    window.show()
    status = app.exec_()

    with open(config_path, "w") as file:
        config.write(file)

    sys.exit(status)
