from datetime import datetime
import json
import logging
import dbus
import dbus.mainloop.glib

from PySide2 import QtCore, QtGui, QtWidgets

from config import config
from SobolDialog import SobolDialog
from AdminChoicePage import AdminChoicePage
from BoardInitPage import BoardInitPage
from BoardSettingsPage import BoardSettingsPage
from ForcePasswdChangePage import ForcePasswdChangePage
from IdWaitPage import IdWaitPage
from PasswdWaitPage import PasswdWaitPage
from UserChoicePage import UserChoicePage
from AdminPasswdChangePage import AdminPasswdChangePage
from UserPasswdChangePage import UserPasswdChangePage
from AdminRegistrationWizard import AdminRegistrationWizard
from UserRegistrationWizard import UserRegistrationWizard


dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
service_object = bus.get_object('ru.navis.ibutton2dbus', '/ru/navis/ibutton2dbus')


class MainWindow(QtWidgets.QMainWindow):
    # Сигнал "предъявления" iButton
    ibuttonPresented = QtCore.Signal(dict)

    def __init__(self):
        super().__init__()
        
        self.setWindowIcon(QtGui.QIcon("../img/sobol.png"))
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.stack = QtWidgets.QStackedWidget()
        self.layout.addWidget(self.stack)

        self.board_init_page = BoardInitPage()
        self.board_init_page.adminRegistrationRequested[bool].connect(self.show_admin_registration_wizard)
        self.board_init_page.boardInitCompleted.connect(self.close)
        self.stack.addWidget(self.board_init_page)

        self.id_wait_page = IdWaitPage()
        self.id_wait_page.ibuttonPresented.connect(lambda: self.set_page(self.passwd_wait_page))
        self.stack.addWidget(self.id_wait_page)

        self.passwd_wait_page = PasswdWaitPage()
        self.passwd_wait_page.passwdEntered[str].connect(self.authenticate_credentials)
        self.stack.addWidget(self.passwd_wait_page)

        self.admin_choice_page = AdminChoicePage()
        self.admin_choice_page.sys_load_requested.connect(self.sys_load)
        self.admin_choice_page.show_settings_requested.connect(lambda: self.set_page(self.board_settings_page))
        self.stack.addWidget(self.admin_choice_page)

        self.user_choice_page = UserChoicePage()
        self.user_choice_page.sys_load_requested.connect(self.sys_load)
        self.user_choice_page.user_passwd_change_requested.connect(lambda: self.set_page(self.user_passwd_change_page))
        self.stack.addWidget(self.user_choice_page)

        self.user_passwd_change_page = UserPasswdChangePage()
        self.user_passwd_change_page.userPasswdChangeCompleted.connect(self.set_ibutton_data)
        self.user_passwd_change_page.userPasswdChangeCanceled.connect(lambda: self.set_page(self.user_choice_page))
        self.stack.addWidget(self.user_passwd_change_page)

        self.force_passwd_change_page = ForcePasswdChangePage()
        self.force_passwd_change_page.userPasswdChangeCompleted.connect(self.set_ibutton_data)
        self.force_passwd_change_page.userPasswdChangeCanceled.connect(lambda: self.set_page(self.board_settings_page))
        self.stack.addWidget(self.force_passwd_change_page)

        self.board_settings_page = BoardSettingsPage()
        self.board_settings_page.sys_load_panel.sys_load_requested.connect(self.sys_load)
        self.board_settings_page.users_list_panel.userRegistrationRequested.connect(self.show_user_registration_wizard)
        self.board_settings_page.users_list_panel.forcePasswdChangeRequested[str].connect(self.show_force_passwd_change_wizard)
        self.board_settings_page.passwd_change_panel.adminPasswdChangeRequested.connect(lambda: self.set_page(self.admin_passwd_change_page))
        self.board_settings_page.service_operations_panel.boardInitRequested.connect(self.init_board)
        self.stack.addWidget(self.board_settings_page)

        self.admin_registration_wizard = AdminRegistrationWizard()
        self.admin_registration_wizard.adminRegistrationСompleted[str, str, dict].connect(self.complete_admin_registration)
        self.admin_registration_wizard.adminRegistrationСanceled.connect(self.cancel_admin_registration)
        self.stack.addWidget(self.admin_registration_wizard)

        self.admin_passwd_change_page = AdminPasswdChangePage()
        self.admin_passwd_change_page.adminPasswdChangeCompleted.connect(self.set_ibutton_data)
        self.admin_passwd_change_page.adminPasswdChangeCanceled.connect(lambda: self.set_page(self.board_settings_page))
        self.stack.addWidget(self.admin_passwd_change_page)

        self.user_registration_wizard = UserRegistrationWizard()
        self.user_registration_wizard.userRegistrationСompleted[str, str, dict].connect(self.complete_user_registration)
        self.user_registration_wizard.userRegistrationСanceled.connect(self.cancel_user_registration)
        self.stack.addWidget(self.user_registration_wizard)

        # В зависимости от того инициализирован комплекс или нет,
        # показать страницу инициализации или ожидания iButton
        if config.admins:
            self.set_page(self.id_wait_page)
        else:
            self.set_page(self.board_init_page)

        # Восстановление настроек окна
        self.setWindowTitle(config.window_title)
        self.setGeometry(config.window_geometry)
        self.restoreState(bytearray(config.window_state))

        try:
            # Установить функцию обратного вызова для обработки сигнала ibutton2dbus
            bus.add_signal_receiver(
                self.ibutton_signal_handler,
                bus_name='ru.navis.ibutton2dbus',
                signal_name="IButtonSignal"
            )
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
        index = next((i for i, user in enumerate(config.users) if user.get("id") == self.message["id"]), None)
        # Проверить, что введенный и записанный в ibutton пароли совпадают
        if passwd == self.message["passwd"]:
            # Проверить принадлежность предъявленного id администратору
            if self.message["id"] in config.admins:
                # Добавить в журнал запись об успешном входе администратора (key="4")
                self.board_settings_page.events_journal_panel.add_event(["Администратор", self.message["id"], "4", "1"])
                self.admin_choice_page.admin_id_value.setText(self.message["id"])
                # Перейти на страницу выбора действий, доступных администратору
                self.set_page(self.admin_choice_page)
                return
            # Проверить принадлежность предъявленного id пользователю
            if index is not None:
                # Если пользователь заблокирован вывести сообщение и перейти на начальную страницу
                if config.users[index]["user_status"]:
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
                config.users[index]["failed_logins"] = 0
                config.users[index]["total_logins"] += 1
                config.users[index]["last_login_datetime"] = datetime.now().strftime("%H:%M %Y/%m/%d")

                self.set_page(self.user_choice_page)
                return
        # Неправильный пароль или идентификатор отсутсвует в списках admins и users
        config.failed_logins += 1
        # Проверить принадлежность предъявленного id пользователю
        if index is not None:
            # Добавить в журнал запись об неуспешном входе пользователя (key="5") и увеличить счетчик неудачных попыток входа
            self.board_settings_page.events_journal_panel.add_event([self.message["user_name"], self.message["id"], "5", "0"])
            config.users[index]["failed_logins"] += 1
            # Заблокировать пользователя, если превышено максимальное число неверных попыток входа
            try:
                if config.users[index]["failed_logins"] > int(config.get("common_parms_panel", "max_failed_logons_line_edit", fallback="0")):
                    config.users[index]["user_status"] = 1
                    logging.debug(f"User {config.users[index]['user_name']} was blocked")
            except (configparser.NoOptionError, NoSectionError) as e:
                logging.debug(e)
        # Проверить принадлежность предъявленного id администратору
        elif self.message["id"] in config.admins:
            # Добавить в журнал запись о неуспешном входе администратора (key="4")
            self.board_settings_page.events_journal_panel.add_event(["Администратор", self.message["id"], "4", "0"])
            
        dialog = SobolDialog("Ошибка", "Неверный идентификатор или пароль", parent=self)
        dialog.exec_()
        self.set_page(self.id_wait_page)

    def show_user_registration_wizard(self):
        """Запустить мастер регистрации пользователя"""
        self.set_page(self.user_registration_wizard)

    def show_force_passwd_change_wizard(self, user_name):
        self.force_passwd_change_page.set_user_name(user_name)
        self.set_page(self.force_passwd_change_page)

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
        config.admins.append(message["id"])
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
        config.admins = []
        config.users = []
        self.set_page(self.board_init_page)

    def sys_load(self):
        """Завершить работу имитатора"""
        self.close()

    def closeEvent(self, event):
        """Сохранить настройки приложения"""
        # Создать обязательные секции, если отсутствуют
        for section in ["window", "general"]:
            if not config.has_section(section):
                config.add_section(section)

        config.window_geometry = self.geometry().getRect()
        config.window_state = int(self.windowState())
      
        # Сохранить журнал событий
        self.board_settings_page.events_journal_panel.model.save()
