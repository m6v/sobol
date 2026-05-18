from datetime import datetime
import logging

from PySide2.QtCore import Qt
from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QPalette, QImage, QBrush, QShowEvent

from config import config
from UiLoader import UiLoader


class UserChoicePage(QtWidgets.QWidget):
    """Страница выбора действий пользователя.
    При открытии в атрибут self.uindex записывается номер записи в списке пользователей"""
    sys_load_requested = QtCore.Signal()
    user_passwd_change_requested = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/UserChoicePage.ui", self)

        self.setStyleSheet("""
            QPushButton { border: 2px solid white; color: white; }
            QLabel { color: white; }
            """)

        self.sys_load_push_button.clicked.connect(self.sys_load_requested.emit)
        self.change_passwd_push_button.clicked.connect(lambda: self.user_passwd_change_requested.emit(self.user_name))

    def resizeEvent(self, event):
        palette = QPalette()
        img = QImage("../img/background.png")
        # Если нужно сохранять пропорции, то вместо IgnoreAspectRatio
        # использовать KeepAspectRatioByExpanding
        scaled = img.scaled(self.size(), Qt.IgnoreAspectRatio)
        palette.setBrush(QPalette.Window, QBrush(scaled))
        self.setPalette(palette)

    def showEvent(self, event: QShowEvent):
        """Показать сведения о пользователе self.index которого передан при открытии панели"""
        index = self.index
        self.user_name_value.setText(config.users[index]["user_name"])
        self.user_id_value.setText(config.users[index]["id"])
        self.user_datetime_value.setText(datetime.now().strftime("%H:%M %Y/%m/%d"))
        self.user_last_datetime_value.setText(config.users[index]["last_login_datetime"])
        self.user_logins_count_value.setText(str(config.users[index]["total_logins"]))

        # Сбросить счетчик неудачных попыток входа, инкрементировать счетчик
        # количества успешных попыток входа, изменить время последнего входа
        config.users[index]["failed_logins"] = 0
        config.users[index]["total_logins"] += 1
        config.users[index]["last_login_datetime"] = datetime.now().strftime("%H:%M %Y/%m/%d")

        passwd_age = config.get("passwd_parms_panel", "passwd_age_line_edit", fallback="")
        # Если число дней действия пароля задано, вывести сколько осталось
        if passwd_age:
            delta = datetime.now() - datetime.strptime(config.users[index]["passwd_datetime"], "%H:%M %Y/%m/%d")
            passwd_expiration_days = int(passwd_age) - delta.days
            if passwd_expiration_days >= 0:
                self.user_remaining_days_value.setText(str(passwd_expiration_days))
            else:
                # TODO Понять, что происходит при истечении срока действия пароля (сообщение о замене, блокировка и т.п.)
                pass
        super().showEvent(event)
