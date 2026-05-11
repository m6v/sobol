import secrets
import string

from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QShowEvent

from UiLoader import UiLoader
from SobolDialog import SobolDialog


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

        self.passwd_line_edit.textChanged[str].connect(self.on_passwd_changed)
        self.passwd_confirm_line_edit.textChanged[str].connect(self.on_passwd_changed)
        self.cancel_push_button_1.clicked.connect(self.adminRegistrationСanceled.emit)
        self.next_push_button.clicked.connect(self.check_passwd)
        self.cancel_push_button_2.clicked.connect(self.adminRegistrationСanceled.emit)
        self.finish_push_button.clicked.connect(self.complete_admin_registration)
        self.passwd_gen_push_button.clicked.connect(self.gen_passwd)
        self.show_passwd_radio_button.clicked.connect(self.toggle_user_passwd_visibility)

        # Настроить таблицу со списком операций при регистрации администратора
        self.table_widget.verticalHeader().hide()
        self.table_widget.insertRow(0)
        self.table_widget.setItem(0, 0, QtWidgets.QTableWidgetItem("Предъявите персональный идентификатор"))
        self.table_widget.resizeColumnsToContents()

    def check_passwd(self):
        """Проверить совпадение пароля в обоих полях ввода и его соответствие требованиям сложности"""
        if self.passwd_line_edit.text() != self.passwd_confirm_line_edit.text():
            dialog = SobolDialog("Ошибка", "Введенные пароли не совпадают, повторите ввод!")
            dialog.exec_()
            return
        self.stacked_widget.setCurrentIndex(1)

    def on_ibutton_presented(self, message):
        # Сохранить идентификатор предъявленной ibutton
        self.message = message
        row = self.table_widget.rowCount() - 1
        self.table_widget.setItem(row, 1, QtWidgets.QTableWidgetItem(message["id"]))
        self.table_widget.setItem(row, 2, QtWidgets.QTableWidgetItem("Администратор зарегистирован"))
        self.table_widget.resizeColumnsToContents()
        self.finish_push_button.setEnabled(True)

    def complete_admin_registration(self):
        """Подать сигнал о завершении работы мастера"""
        self.adminRegistrationСompleted.emit("Администратор", self.passwd_line_edit.text(), self.message)

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
        # TODO Считать из настроек длину пароля и подставить параметром в gen_password
        passwd = gen_password()
        self.passwd_line_edit.setText(passwd)
        self.passwd_confirm_line_edit.setText(passwd)
        self.show_passwd_radio_button.setChecked(True)
        self.toggle_user_passwd_visibility()

    def on_passwd_changed(self):
        """Изменить состояние кнопки "Вперед" при наличии символов в обоих полях ввода пароля"""
        if len(self.passwd_line_edit.text()) != 0 and len(self.passwd_confirm_line_edit.text()) != 0:
            self.next_push_button.setEnabled(True)
        else:
            self.next_push_button.setEnabled(False)

    def showEvent(self, event: QShowEvent):
        self.stacked_widget.setCurrentIndex(0)
        self.passwd_line_edit.setText("")
        self.passwd_confirm_line_edit.setText("")
        # Вызвать базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
