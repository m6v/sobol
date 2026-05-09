import configparser
from datetime import datetime
import json
import logging

import dbus
import dbus.mainloop.glib

from PySide2 import QtCore, QtGui, QtWidgets


import constants
from AdminChoicePage import AdminChoicePage
from BoardInitPage import BoardInitPage
from BoardSettingsPage import BoardSettingsPage
from IdWaitPage import IdWaitPage
from PasswdWaitPage import PasswdWaitPage
from UserChoicePage import UserChoicePage
from AdminPasswdChangePage import AdminPasswdChangePage
from UserPasswdChangePage import UserPasswdChangePage

from AdminRegistrationWizard import AdminRegistrationWizard
from UserRegistrationWizard import UserRegistrationWizard

from SobolDialog import SobolDialog


dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
service_object = bus.get_object('ru.navis.ibutton2dbus', '/ru/navis/ibutton2dbus')

class MainWindow(QtWidgets.QMainWindow):
    # Сигнал "предъявления" iButton
    ibuttonPresented = QtCore.Signal(dict)

    def __init__(self, config):
        super().__init__()

        self.config = config

        self.setWindowIcon(QtGui.QIcon("../img/sobol.png"))
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.stack = QtWidgets.QStackedWidget()
        self.layout.addWidget(self.stack)

        self.board_init_page = BoardInitPage(config)
        self.board_init_page.adminRegistrationRequested[bool].connect(self.show_admin_registration_wizard)
        self.board_init_page.boardInitCompleted.connect(self.close)

        self.id_wait_page = IdWaitPage(config)
        self.id_wait_page.ibuttonPresented.connect(lambda: self.set_page(self.passwd_wait_page))
        
        self.passwd_wait_page = PasswdWaitPage(config, self)
        self.passwd_wait_page.passwdEntered[str].connect(self.authenticate_credentials)

        self.admin_choice_page = AdminChoicePage(config)
        self.admin_choice_page.sys_load_requested.connect(self.sys_load)
        self.admin_choice_page.show_settings_requested.connect(lambda: self.set_page(self.board_settings_page))
        
        self.user_choice_page = UserChoicePage(config)
        self.user_choice_page.sys_load_requested.connect(self.sys_load)
        self.user_choice_page.user_passwd_change_requested.connect(lambda: self.set_page(self.user_passwd_change_page))

        self.user_passwd_change_page = UserPasswdChangePage(config)
        self.user_passwd_change_page.userPasswdChangeCompleted.connect(self.set_ibutton_data)
        self.user_passwd_change_page.userPasswdChangeCanceled.connect(lambda: self.set_page(self.user_choice_page))

        self.board_settings_page = BoardSettingsPage(config)
        self.board_settings_page.sys_load_panel.sys_load_requested.connect(self.sys_load)
        self.board_settings_page.users_list_panel.userRegistrationRequested.connect(self.show_user_registration_wizard)
        self.board_settings_page.passwd_change_panel.adminPasswdChangeRequested.connect(lambda: self.set_page(self.admin_passwd_change_page))
        self.board_settings_page.service_operations_panel.boardInitRequested.connect(self.init_board)

        self.admin_registration_wizard = AdminRegistrationWizard(config)
        self.admin_registration_wizard.adminRegistrationСompleted[str, str, dict].connect(self.complete_admin_registration)
        self.admin_registration_wizard.adminRegistrationСanceled.connect(self.cancel_admin_registration)

        self.admin_passwd_change_page = AdminPasswdChangePage(config)
        self.admin_passwd_change_page.adminPasswdChangeCompleted.connect(self.set_ibutton_data)
        self.admin_passwd_change_page.adminPasswdChangeCanceled.connect(lambda: self.set_page(self.board_settings_page))

        self.user_registration_wizard = UserRegistrationWizard(config)
        self.user_registration_wizard.userRegistrationСompleted[str, str, dict].connect(self.complete_user_registration)
        self.user_registration_wizard.userRegistrationСanceled.connect(self.cancel_user_registration)

        self.stack.addWidget(self.board_init_page)
        self.stack.addWidget(self.id_wait_page)
        self.stack.addWidget(self.passwd_wait_page)
        self.stack.addWidget(self.admin_choice_page)
        self.stack.addWidget(self.admin_passwd_change_page)
        self.stack.addWidget(self.user_choice_page)
        self.stack.addWidget(self.user_passwd_change_page)
        self.stack.addWidget(self.board_settings_page)
        self.stack.addWidget(self.admin_registration_wizard)
        self.stack.addWidget(self.user_registration_wizard)

        try:
            # Список из идентификаторов iButton зарегистрированных администраторов
            self.admins = json.loads(self.config.get("general", "admins", fallback="[]"))
            # Список из идентификаторов iButton зарегистрированных пользователей
            self.users = json.loads(self.config.get("general", "users", fallback="[]"))
            # Суммарное кол-во неудачных попыток входа (с момента инициализации)
            self.failed_logins = int(self.config.get("general", "failed_logins", fallback="0"))
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
            # Здесь при необходимости можно создать отсутствующую секцию конфига
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
        self.ibuttonPresented.emit(message)

    def set_page(self, widget):
        """Отобразить страницу widget"""
        # Отключить сигнал у предыдущего виджета
        try:
            self.ibuttonPresented[dict].disconnect(self.stack.currentWidget().on_ibutton_presented)
        except (AttributeError, RuntimeError) as e:
            logging.debug(e)
        # Сделать текщим widget и установить сигнал
        self.stack.setCurrentWidget(widget)
        try:
            # Соединяить сигнал предъявления ibutton с методом нового виджета
            # Если обработчика нет, игнорируем исключение
            self.ibuttonPresented[dict].connect(widget.on_ibutton_presented)
        except AttributeError as e:
            logging.debug(e)

    def authenticate_credentials(self, passwd):
        # Получить индекс элемента с предъявленным идентификатором в списке users или None, если не найден
        index = next((i for i, user in enumerate(self.users) if user.get("id") == self.message["id"]), None)
        # Проверить, что введенный и записанный в ibutton пароли совпадают
        if passwd == self.message["passwd"]:
            # Проверить принадлежность предъявленного id администратору
            if self.message["id"] in self.admins:
                # Добавить в журнал запись об успешном входе администратора (key="4")
                self.board_settings_page.events_journal_panel.add_event(["Администратор", self.message["id"], "4", "1"])
                self.admin_choice_page.admin_id_value.setText(self.message["id"])
                # Перейти на страницу выбора действий, доступных администратору
                self.set_page(self.admin_choice_page)
                return
            # Проверить принадлежность предъявленного id пользователю
            if index is not None:
                # Если пользователь заблокирован вывести сообщение и перейти на начальную страницу
                if self.users[index]["user_status"]:
                    dialog = SobolDialog("Ошибка", "Вход в систему запрещен администратором", parent=self)
                    dialog.exec_()
                    self.set_page(self.id_wait_page)
                    return
                # TODO Показать статистику, только если установлен соответствующий параметр (self.common_parms_panel.show_stats_check_box=True)
                pass
                # Добавить в журнал запись об успешном входе пользователя (key="5")
                self.board_settings_page.events_journal_panel.add_event([self.message["user_name"], self.message["id"], "5", "1"])

                # Сбросить счетчик неудачных попыток входа, инкрементировать счетчик
                # количества успешных попыток входа, изменить время последнего входа
                self.users[index]["failed_logins"] = 0
                self.users[index]["total_logins"] += 1
                self.users[index]["last_login_datetime"] = datetime.now().strftime("%H:%M %Y/%m/%d")
                # Запомнить измененные параметры учетной записи
                self.config.set("general", "users", json.dumps(self.users, ensure_ascii=False))

                self.set_page(self.user_choice_page)
                return
        # Неправильный пароль или идентификатор отсутсвует в списках admins и users
        logging.info(f"Fail login, user index {index}")
        self.failed_logins += 1
        self.config.set("general", "failed_logins", str(self.failed_logins))
        # Проверить принадлежность предъявленного id пользователю
        if index is not None:
            # Добавить в журнал запись об неуспешном входе пользователя (key="5") и увеличить счетчик неудачных попыток входа
            self.board_settings_page.events_journal_panel.add_event([self.message["user_name"], self.message["id"], "5", "0"])
            self.users[index]["failed_logins"] += 1
            # Заблокировать пользователя, если превышено максимальное число неверных попыток входа
            try:
                if self.users[index]["failed_logins"] > int(self.config.get("common_parms_panel", "max_failed_logons_line_edit", fallback="0")):
                    self.users[index]["user_status"] = 1
                    logging.debug(f"Пользователь {self.users[index]['user_name']} заблокирован")
            except (configparser.NoOptionError, NoSectionError) as e:
                logging.debug(e)
            # Запомнить измененные параметры учетной записи
            self.config.set("general", "users", json.dumps(self.users, ensure_ascii=False))
        # Проверить принадлежность предъявленного id администратору
        elif self.message["id"] in self.admins:
            # Добавить в журнал запись о неуспешном входе администратора (key="4")
            self.board_settings_page.events_journal_panel.add_event(["Администратор", self.message["id"], "4", "0"])
            
        dialog = SobolDialog("Ошибка", "Неверный идентификатор или пароль", parent=self)
        dialog.exec_()
        self.set_page(self.id_wait_page)

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
        self.config.set("general", "admins", json.dumps(self.admins, ensure_ascii=False))
        # Вызвать метод SetIButtonData, зарегистрированный в dbus
        # для записи в предъявленную ibutton имени и пароля администратора
        service_object.SetIButtonData({
            "id": self.message["id"],
            "user_name": user_name,
            "passwd": passwd
        })
        self.set_page(self.board_init_page)

    def cancel_admin_registration(self):
        """Отменить регистрацию администратора"""
        self.board_init_page.show_init_panel()
        self.set_page(self.board_init_page)

    def set_ibutton_data(self, user_name, passwd, message):
        """Записать в iButton новый пароль пользователя (администратора)"""
        service_object.SetIButtonData({
            "id": self.message["id"],
            "user_name": user_name,
            "passwd": passwd
        })

    def init_board(self):
        """Программная инициализация платы"""
        self.admins = []
        self.users = []
        self.config.set("general", "admins", json.dumps(self.admins, ensure_ascii=False))
        self.config.set("general", "users", json.dumps(self.users, ensure_ascii=False))
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
        # Сохранить журнал событий
        self.board_settings_page.events_journal_panel.model.save()
