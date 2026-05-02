import configparser
import json
import logging
import secrets
import string

import dbus
import dbus.mainloop.glib

from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QShowEvent

from UiLoader import UiLoader

from SobolDialog import SobolDialog

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
service_object = bus.get_object('ru.navis.ibutton2dbus', '/ru/navis/ibutton2dbus')

def gen_password(length=8):
    """Сгенерировать пароль заданной длины"""
    if length < 4:
        raise ValueError("Length must be >= 4")

    chars = {
        "lower": string.ascii_lowercase,
        "upper": string.ascii_uppercase,
        "digit": string.digits,
        "symbol": string.punctuation
    }

    password = [
        secrets.choice(chars["lower"]),
        secrets.choice(chars["upper"]),
        secrets.choice(chars["digit"]),
        secrets.choice(chars["symbol"]),
    ]

    all_chars = ''.join(chars.values())
    password += [secrets.choice(all_chars) for _ in range(length - 4)]
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


class AdminRegistrationWizard(QtWidgets.QWidget):
    """Страница регистрации администратора"""
    adminRegistrationСompleted = QtCore.Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.config = config

        self.loader = UiLoader()
        self.loader.loadUi("../ui/AdminRegistrationWizard.ui", self)
        
        # Список из идентификаторов iButton зарегистрированных администраторов
        self.admins = json.loads(self.config.get("general", "admins", fallback="[]"))

        self.passwd_line_edit.textChanged[str].connect(self.passwd_changed)
        self.passwd_confirm_line_edit.textChanged[str].connect(self.passwd_changed)
        self.next_push_button.clicked.connect(self.check_passwd)
        self.finish_push_button.clicked.connect(self.complete_admin_registration)
        self.passwd_gen_push_button.clicked.connect(self.gen_passwd)
        self.show_passwd_radio_button.clicked.connect(self.toggle_user_passwd_visibility)

    def check_passwd(self):
        """Проверить совпадение пароля в обоих полях ввода и его соответствие требованиям сложности"""
        if self.passwd_line_edit.text() != self.passwd_confirm_line_edit.text():
            # QtWidgets.QMessageBox.warning(self, "Ошибка", "Введенные пароли не совпадают, повторите ввод!", QtWidgets.QMessageBox.Ok)
            dialog = SobolDialog("Ошибка", "Введенные пароли не совпадают, повторите ввод!")
            dialog.exec_()
            return
        self.stacked_widget.setCurrentIndex(1)

    def on_ibutton_presented(self, message):
        # Сохранить идентификатор предъявленной ibutton
        self.message = message
        self.finish_push_button.setEnabled(True)

    def complete_admin_registration(self):
        """Зарегистрировать администратора и подать сигнал о завершении работы мастера"""
        self.admins.append(self.message['id'])
        # Вызвать метод SetIButtonData, зарегистрированный в dbus
        # для записи в предъявленную ibutton имени и пароля администратора
        service_object.SetIButtonData({
            "id": self.message["id"],
            "user_name": "Администратор",
            "passwd": self.passwd_line_edit.text()
        })
        self.adminRegistrationСompleted.emit()

    def toggle_user_passwd_visibility(self):
        """Переключить видимость пароля пользователя в полях ввода"""
        if self.show_passwd_radio_button.isChecked():
            self.passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.passwd_confirm_line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
            self.passwd_confirm_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)

    def gen_passwd(self):
        """Сгенерировать пароль пользователя и показать его в полях ввода"""
        # TODO Считать из начтроек длину пароля и подставить параметром в gen_password
        passwd = gen_password()
        self.passwd_line_edit.setText(passwd)
        self.passwd_confirm_line_edit.setText(passwd)
        self.show_passwd_radio_button.setChecked(True)
        self.toggle_user_passwd_visibility()

    def passwd_changed(self):
        """Изменить состояние кнопки "Вперед" при наличии символов в обоих полях ввода пароля"""
        if len(self.passwd_line_edit.text()) != 0 and len(self.passwd_confirm_line_edit.text()) != 0:
            self.next_push_button.setEnabled(True)
        else:
            self.next_push_button.setEnabled(False)

    def showEvent(self, event: QShowEvent):
        self.stacked_widget.setCurrentIndex(0)
        # TODO Далее нужно очистить все элементы ввода от предыдущих итераций
        # Обязательно вызываем базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
