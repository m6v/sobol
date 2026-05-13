from datetime import datetime
import logging

import dbus
import dbus.mainloop.glib

from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QShowEvent

from config import config
from Toggle import Toggle
from UiLoader import UiLoader

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
service_object = bus.get_object('ru.navis.ibutton2dbus', '/ru/navis/ibutton2dbus')


class UsersListPanel(QtWidgets.QWidget):
    """Панель со списком и настройками учетных записей пользователей"""
    userRegistrationRequested = QtCore.Signal()
    userPasswdChangeRequested = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        # Загрузить интерфейс и зарегистрировать кастомный класс Toggle
        self.loader.loadUi("../ui/UsersListPanel.ui", self, Toggle)

        self.user_list_widget.itemClicked.connect(self.show_user_parms)
        self.user_list_widget.itemActivated.connect(self.show_user_parms)

        self.add_user_push_button.clicked.connect(self.userRegistrationRequested.emit)
        self.del_user_push_button.clicked.connect(self.del_user)
        self.del_all_users_push_button.clicked.connect(self.del_all_users)
        self.change_passwd_push_button.clicked.connect(self.change_passwd)
        self.save_push_button.clicked.connect(self.save_user_parms)

    def show_user_parms(self):
        """Показать настройки выбранного в списке пользователя"""
        index = self.user_list_widget.currentRow()
        logging.debug(f"User '{config.users[index]['user_name']}' is selected")
        user = config.users[index]
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
        config.users[index]["ext_media_prohib"] = self.ext_media_prohib.isChecked()
        config.users[index]["ch_passwd_prohib"] = self.ch_passwd_prohib.isChecked()
        config.users[index]["passwd_age_limit"] = self.passwd_age_limit.isChecked()
        config.users[index]["user_id_change"] = self.user_id_change.isChecked()
        config.users[index]["user_status"] = self.user_status.currentIndex()
        config.users[index]["integrity_ctl_mode"] = self.integrity_ctl_mode.currentIndex()

    def update_user_list_panel(self):
        """Обновить панель со списком пользователей"""
        # Сохранить список пользователей в конфигурации
        self.user_list_widget.clear()
        self.del_user_push_button.setEnabled(bool(config.users))
        self.del_all_users_push_button.setEnabled(bool(config.users))
        self.change_passwd_push_button.setEnabled(bool(config.users))
        self.user_count_label.setText(str(len(config.users)))
        # Если зарегистрированных пользователей нет, то выйти
        if not config.users:
            # TODO Установить дефолтные настройки пользователя и отключить панель настроек
            return
        for user in config.users:
            self.user_list_widget.addItem(user["user_name"])
        self.user_list_widget.setCurrentRow(0)
        self.show_user_parms()

    def add_user(self, user_name, passwd, message):
        """Добавить пользователя user_name с паролем passwd"""
        config.users.append({
            "id": message["id"],
            "user_name": user_name,
            "passwd_datetime": datetime.now().strftime("%H:%M %Y/%m/%d"),
            "last_login_datetime": "00:00 1970/01/01",
            "total_logins": 0,
            "failed_logins": 0,
            "ext_media_prohib": True,
            "ch_passwd_prohib": False,
            "passwd_age_limit": True,
            "user_id_change": True,
            "user_status": 0,
            "integrity_ctl_mode": 0
        })

        # Вызвать метод для записи в предъявленную ibutton имени и пароля пользователя
        service_object.SetIButtonData({
            "id": message["id"],
            "user_name": user_name,
            "passwd": passwd
        })

    def del_user(self):
        """Удалить выбранного пользователя"""
        index = self.user_list_widget.currentRow()
        config.users.pop(index)
        self.update_user_list_panel()

    def del_all_users(self):
        """Удалить всех пользователей"""
        config.users.clear()
        self.update_user_list_panel()

    def change_passwd(self):
        """Отправить сигнал о принудительной смене пароля выбранным пользователем"""
        index = self.user_list_widget.currentRow()
        self.userPasswdChangeRequested.emit(config.users[index]['user_name'])

    def showEvent(self, event: QShowEvent):
        self.update_user_list_panel()
        # Вызвать базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
