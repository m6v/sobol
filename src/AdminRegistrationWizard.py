import logging
import secrets
import string

from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QShowEvent

from UiLoader import UiLoader
from SobolDialog import SobolDialog

PRIMARY_REGISTRATION_PANEL = 0
SECONDARY_REGISTRATION_PANEL = 1
ID_WAIT_PANEL = 2

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
    """Мастер регистрации администратора"""
    adminRegistrationСompleted = QtCore.Signal(str, str, dict)
    adminRegistrationСanceled = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/AdminRegistrationWizard.ui", self)

        self.new_passwd_line_edit.textChanged[str].connect(self.on_passwd_changed)
        self.confirm_passwd_line_edit.textChanged[str].connect(self.on_passwd_changed)
        self.cancel_push_button_1.clicked.connect(self.adminRegistrationСanceled.emit)
        self.next_push_button_1.clicked.connect(self.check_passwd)
        self.old_passwd_line_edit.textChanged[str].connect(lambda: self.next_push_button_2.setEnabled(bool(self.old_passwd_line_edit.text())))
        self.cancel_push_button_2.clicked.connect(self.adminRegistrationСanceled.emit)
        self.next_push_button_2.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(ID_WAIT_PANEL))
        self.cancel_push_button_3.clicked.connect(self.adminRegistrationСanceled.emit)
        self.finish_push_button_3.clicked.connect(self.complete_admin_registration)
        self.passwd_gen_push_button.clicked.connect(self.gen_passwd)
        self.show_passwd_radio_button.clicked.connect(self.toggle_user_passwd_visibility)

        # Настроить таблицу со списком операций при регистрации администратора
        self.table_widget.verticalHeader().hide()
        self.table_widget.insertRow(0)
        self.table_widget.setItem(0, 0, QtWidgets.QTableWidgetItem("Предъявите персональный идентификатор"))
        self.table_widget.resizeColumnsToContents()

    def check_passwd(self):
        """Проверить совпадение пароля в обоих полях ввода и его соответствие требованиям сложности"""
        if self.new_passwd_line_edit.text() != self.confirm_passwd_line_edit.text():
            dialog = SobolDialog("Ошибка", "Введенные пароли не совпадают, повторите ввод!")
            dialog.exec_()
            return
        self.stacked_widget.setCurrentIndex(ID_WAIT_PANEL)

    def on_ibutton_presented(self, message):
        # Сохранить идентификатор предъявленной ibutton
        self.message = message
        if not self.is_primary_admin_registration:
            if self.old_passwd_line_edit.text() != self.message["passwd"]:
                dialog = SobolDialog("Ошибка", "Неверный идентификатор или пароль")
                dialog.exec_()
                return
            # Оставить старый пароль
            self.new_passwd_line_edit.setText(self.old_passwd_line_edit.text())
        row = self.table_widget.rowCount() - 1
        self.table_widget.setItem(row, 1, QtWidgets.QTableWidgetItem(message["id"]))
        self.table_widget.setItem(row, 2, QtWidgets.QTableWidgetItem("Администратор зарегистирован"))
        self.table_widget.resizeColumnsToContents()
        self.finish_push_button_3.setEnabled(True)

    def complete_admin_registration(self):
        """Подать сигнал о завершении работы мастера"""
        self.adminRegistrationСompleted.emit("Администратор", self.new_passwd_line_edit.text(), self.message)

    def toggle_user_passwd_visibility(self):
        """Переключить видимость пароля пользователя в полях ввода"""
        if self.show_passwd_radio_button.isChecked():
            self.new_passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.confirm_passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.new_passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
            self.confirm_passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)

    def gen_passwd(self):
        """Сгенерировать пароль пользователя и показать его в полях ввода"""
        # TODO Считать из настроек длину пароля и подставить параметром в gen_password
        passwd = gen_password()
        self.new_passwd_line_edit.setText(passwd)
        self.confirm_passwd_line_edit.setText(passwd)
        self.show_passwd_radio_button.setChecked(True)
        self.toggle_user_passwd_visibility()

    def on_passwd_changed(self):
        """Изменить состояние кнопки "Вперед" при наличии символов в обоих полях ввода пароля"""
        if len(self.new_passwd_line_edit.text()) != 0 and len(self.confirm_passwd_line_edit.text()) != 0:
            self.next_push_button_1.setEnabled(True)
        else:
            self.next_push_button_1.setEnabled(False)

    def showEvent(self, event: QShowEvent):
        if self.is_primary_admin_registration:
            self.stacked_widget.setCurrentIndex(PRIMARY_REGISTRATION_PANEL)
        else:
            self.stacked_widget.setCurrentIndex(SECONDARY_REGISTRATION_PANEL)
        self.old_passwd_line_edit.setText("")
        self.new_passwd_line_edit.setText("")
        self.confirm_passwd_line_edit.setText("")
        self.finish_push_button_3.setEnabled(False)
        # Вызвать базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
