import configparser
from datetime import datetime
import json
import logging

import dbus
import dbus.mainloop.glib

from PySide2 import QtCore, QtWidgets

from AdminChoicePage import AdminChoicePage
from BoardInitPage import BoardInitPage
from IdWaitPage import IdWaitPage
from BoardSettingsPage import BoardSettingsPage

from AdminRegistrationWizard import AdminRegistrationWizard
from UserRegistrationWizard import UserRegistrationWizard

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
service_object = bus.get_object('ru.navis.ibutton2dbus', '/ru/navis/ibutton2dbus')

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
        self.board_init_page.adminRegistrationRequested[bool].connect(self.show_admin_registration_wizard)

        self.id_wait_page = IdWaitPage(config)
        self.id_wait_page.ibutton_presented.connect(lambda: self.set_page(self.admin_choice_page))

        self.admin_choice_page = AdminChoicePage(config)
        self.admin_choice_page.sys_load_requested.connect(self.sys_load)
        self.admin_choice_page.show_settings_requested.connect(lambda: self.set_page(self.board_settings_page))

        self.board_settings_page = BoardSettingsPage(config)
        self.board_settings_page.sys_load_panel.sys_load_requested.connect(self.sys_load)
        self.board_settings_page.users_list_panel.userRegistrationRequested.connect(self.show_user_registration_wizard)

        self.admin_registration_wizard = AdminRegistrationWizard(config)
        self.admin_registration_wizard.adminRegistrationСompleted[str, str, dict].connect(self.complete_admin_registration)

        self.user_registration_wizard = UserRegistrationWizard(config)
        self.user_registration_wizard.userRegistrationСompleted[str, str, dict].connect(self.complete_user_registration)
        self.user_registration_wizard.userRegistrationСanceled.connect(self.cancel_user_registration)

        self.stack.addWidget(self.board_init_page)
        self.stack.addWidget(self.id_wait_page)
        self.stack.addWidget(self.admin_choice_page)
        self.stack.addWidget(self.board_settings_page)
        self.stack.addWidget(self.admin_registration_wizard)
        self.stack.addWidget(self.user_registration_wizard)

        try:
            # Список из идентификаторов iButton зарегистрированных администраторов
            self.admins = json.loads(self.config.get("general", "admins", fallback="[]"))
            # Суммарное кол-во неудачных попыток входа (с момента инициализации)
            self.failed_logins = int(self.config.get("general", "failed_logins", fallback="0"))
            # Имя файла с журналом событий
            self.journal_file = self.config.get("general", "journal_file", fallback="")
        except configparser.NoOptionError as e:
            logging.warning(e)
        except configparser.NoSectionError as e:
            logging.error(e)

        # В зависимости от того инициализирован комплекс или нет,
        # показать страницу инициализации или ожидания iButton
        if self.admins:
            self.set_page(self.id_wait_page)
        else:
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
            # Установить функцию обратного вызова для обработки сигнала ibutton2dbus
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

    def show_user_registration_wizard(self):
        """Запустить мастер регистрации пользователя"""
        self.set_page(self.user_registration_wizard)

    def complete_user_registration(self, user_name, passwd, message):
        """Завершить регистрацию пользователя"""
        # Методы по управлению пользователями реализованы в self.board_settings_page.users_list_panel
        self.board_settings_page.users_list_panel.add_user(user_name, passwd, message)
        self.set_page(self.board_settings_page)

    def cancel_user_registration(self):
        """Отменить регистрацию пользователя"""
        self.set_page(self.board_settings_page)

    def show_admin_registration_wizard(self, is_primary_admin_registration):
        """Запустить мастер регистрации администратора"""
        # TODO В зависимости от is_primary_admin_registration разные действия
        # при первичной регистрации запрашивается и записывается новый пароль,
        # при повторной регистрации запрашивается и проверяется записанный пароль
        self.set_page(self.admin_registration_wizard)

    def complete_admin_registration(self, user_name, passwd, message):
        """Зарегистрировать администратора"""
        self.admins.append(message["id"])
        # Вызвать метод SetIButtonData, зарегистрированный в dbus
        # для записи в предъявленную ibutton имени и пароля администратора
        service_object.SetIButtonData({
            "id": self.message["id"],
            "user_name": user_name,
            "passwd": passwd
        })
        self.set_page(self.board_init_page)

    def sys_load(self):
        """Завершить работу имитатора"""
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

        # Сохранить учетные записи пользователей и суммарное кол-во неудачных попыток входа
        self.config.set("general", "users", json.dumps(self.board_settings_page.users_list_panel.users, ensure_ascii=False))
        self.config.set("general", "admins", json.dumps(self.admins, ensure_ascii=False))
        self.config.set("general", "failed_logins", str(self.failed_logins))
