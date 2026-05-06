import configparser
from datetime import datetime
import json
import logging

from PySide2.QtCore import Qt
from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QPalette, QImage, QBrush, QShowEvent

from UiLoader import UiLoader


class PasswdWaitPage(QtWidgets.QWidget):
    """Страница ожидания ввода пароля"""
    passwdEntered = QtCore.Signal(str)
    adminAuthenticated = QtCore.Signal()
    userAuthenticated = QtCore.Signal()
    authenticationFailed = QtCore.Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.config = config
        self.parent = parent

        self.setAutoFillBackground(True)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/PasswdWaitPage.ui", self)

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

        self.setStyleSheet("""
            QPushButton { border: 2px solid white; color: white; }
            QLabel { color: white; }
            """)

        self.enter_push_button.clicked.connect(self.authenticate_credentials)

    def authenticate_credentials(self):
        """Временное решение с отправкой сигнала, содержащего введенный пароль"""
        passwd = self.passwd_line_edit.text()
        if passwd:
            self.passwdEntered.emit(passwd)
        return
        """Аутентифицировать субъекта и отправить сигнал о результате"""
        # Проблема в том, что многие переменные вне зоны видимости, можно использовать self.parent, но это костыль!
        self.message = self.parent.message
        # Получить индекс элемента с предъявленным идентификатором в списке users или None, если не найден
        index = next((i for i, user in enumerate(self.users) if user.get("id") == self.message["id"]), None)
        # Проверить, что введенный и записанный в ibutton пароли совпадают
        if self.passwd_line_edit.text() == self.message["passwd"]:
            # Проверить принадлежность предъявленного id администратору
            if self.message["id"] in self.admins:
                # Добавить в журнал запись об успешном входе администратора (key="4")
                self.board_settings_page.events_journal_panel.model.add_event(["Администратор", self.message["id"], "4", "1"])
                self.admin_choice_page.admin_id_value.setText(self.message["id"])
                # Отправить сигнал об успешной аутентификации администратора
                self.adminAuthenticated.emit()
                return
            # Проверить принадлежность предъявленного id пользователю
            if index is not None:
                # TODO Проверить, что пользователь не заблокирован (user_status!=0)
                pass
                # TODO Показать статистику, только если установлен соответствующий параметр (self.common_parms_panel.show_stats_check_box=True)
                pass
                # Добавить в журнал запись об успешном входе пользователя (key="5")
                self.board_settings_page.events_journal_panel.model.add_event([self.message["user_name"], self.message["id"], "5", "1"])

                # Сбросить счетчик неудачных попыток входа, инкрементировать счетчик
                # количества успешных попыток входа, изменить время последнего входа
                self.users[index]["failed_logins"] = 0
                self.users[index]["total_logins"] += 1
                self.users[index]["last_login_datetime"] = datetime.now().strftime("%H:%M %Y/%m/%d")
                # Отправить сигнал об успешной аутентификации пользователя
                self.userAuthenticated.emit()
                return
        # Неправильный пароль или идентификатор отсутсвует в списках admins и users
        logging.info(f"Fail login, user index {index}")
        self.failed_logins += 1
        self.config.set("general", "failed_logins", str(self.failed_logins))
        # Проверить принадлежность предъявленного id пользователю
        if index is not None:
            # Добавить в журнал запись об неуспешном входе пользователя (key="5")
            self.board_settings_page.events_journal_panel.model.add_event([self.message["user_name"], self.message["id"], "5", "0"])

            self.users[index]["failed_logins"] += 1
            # TODO Заблокировать пользователя, если превышено максимальное число неверных попыток входа
            pass
        # Проверить принадлежность предъявленного id администратору
        elif self.message["id"] in self.admins:
            # Добавить в журнал запись о неуспешном входе администратора (key="4")
            self.board_settings_page.events_journal_panel.model.add_event(["Администратор", self.message["id"], "4", "0"])
            
        dialog = SobolDialog("Ошибка", "Неверный идентификатор или пароль", parent=self)
        dialog.exec_()
        # Отправить сигнал об неуспешной аутентификации
        self.authenticationFailed.emit()
        # TODO Добавить сохранение self.users в конфиге!

    def resizeEvent(self, event):
        palette = QPalette()
        img = QImage("../img/background.png")
        # Если нужно сохранять пропорции, то вместо IgnoreAspectRatio
        # использовать KeepAspectRatioByExpanding
        scaled = img.scaled(self.size(), Qt.IgnoreAspectRatio)
        palette.setBrush(QPalette.Window, QBrush(scaled))
        self.setPalette(palette)

    def showEvent(self, event: QShowEvent):
        """Стереть введенный во время предыдущей попытки аутентификации пароль"""
        self.passwd_line_edit.setText("")
        # Вызываем базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
