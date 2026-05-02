import configparser
import json
import logging

import dbus
import dbus.mainloop.glib

from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QShowEvent

from Toggle import Toggle
from UiLoader import UiLoader

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()


class UsersListPanel(QtWidgets.QWidget):
    """Панель со списком и настройками учетных записей пользователей"""
    userRegistrationRequested = QtCore.Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.config = config

        self.loader = UiLoader()
        # Загружаем интерфейс и регистрируем кастомный класс Toggle
        self.loader.loadUi("../ui/UsersListPanel.ui", self, Toggle)
        
        # Список из словарей с параметрами зарегистрированных пользователей (идентификатор iButton, имя и др.)
        self.users = json.loads(self.config.get("general", "users", fallback="[]"))

        self.add_user_push_button.clicked.connect(self.userRegistrationRequested.emit)

    def show_user_parms(self, item):
        """Показать настройки выбранного в списке пользователя"""
        index = self.user_list_widget.currentRow()
        logging.debug(f"Select user: {self.users[index]['user_name']}")
        user = self.users[index]
        try:
            self.user_id.setText(user["id"])
            self.user_name.setText(user["user_name"])
            self.last_login_datetime.setText(user["last_login_datetime"])
            self.total_logins.setText(str(user["total_logins"]))
            self.failed_logins.setText(str(user["failed_logins"]))
            self.ext_media_prohib.setChecked(bool(user["ext_media_prohib"]))
            self.ch_passwd_prohib.setChecked(bool(user["ch_passwd_prohib"]))
            self.passwd_age_limit.setChecked(bool(user["passwd_age_limit"]))
            self.user_id_change.setChecked(bool(user["user_id_change"]))
            self.user_status.setCurrentIndex(user["user_status"])
            self.integrity_ctl_mode.setCurrentIndex(user["integrity_ctl_mode"])
        except KeyError as e:
            logging.debug(e)

    def save_user_parms(self):
        """Сохранить настройки выбранного в списке пользователя"""
        index = self.user_list_widget.currentRow()
        logging.info(f"Selected user is {self.users[index]}")
        self.users[index]["ext_media_prohib"] = self.ext_media_prohib.isChecked()
        self.users[index]["ch_passwd_prohib"] = self.ch_passwd_prohib.isChecked()
        self.users[index]["passwd_age_limit"] = self.passwd_age_limit.isChecked()
        self.users[index]["user_id_change"] = self.user_id_change.isChecked()
        self.users[index]["user_status"] = self.user_status.currentIndex()
        self.users[index]["integrity_ctl_mode"] = self.integrity_ctl_mode.currentIndex()

    def update_user_list_panel(self):
        """Обновить панель со списком пользователей"""
        self.user_list_widget.clear()
        # Если зарегистрированных пользователей нет, например,
        # сразу после инициализации, то выйти
        if not self.users:
            return
        for user in self.users:
            self.user_list_widget.addItem(user["user_name"])
        self.user_list_widget.setCurrentRow(0)
        self.show_user_parms(self.user_list_widget.currentItem())

    def del_user(self):
        """Удалить выбранного пользователя"""
        index = self.user_list_widget.currentRow()
        self.users.pop(index)
        self.update_user_list_panel()

    def del_all_users(self):
        """Удалить всех всех пользователей"""
        self.users.clear()
        self.update_user_list_panel()

    def showEvent(self, event: QShowEvent):
        self.update_user_list_panel()
        # Обязательно вызываем базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
