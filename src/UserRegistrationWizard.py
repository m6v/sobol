from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QShowEvent

from UiLoader import UiLoader
from SobolDialog import SobolDialog

USER_NAME_PANEL = 0
REGISTRATION_TYPE_PANEL = 1
NEW_PASSWD_PANEL = 2
OLD_PASSWD_PANEL = 3
ID_PRESENT_PANEL = 4
USER_REGISTERED_PANEL = 5


class UserRegistrationWizard(QtWidgets.QWidget):
    """Мастер регистрации пользователя"""
    userRegistrationСompleted = QtCore.Signal(str, str, dict)
    userRegistrationСanceled = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/UserRegistrationWizard.ui", self)

        self.user_name_line_edit.textChanged[str].connect(self.on_user_name_changed)
        self.cancel_push_button_1.clicked.connect(self.cancel_user_registration)
        self.next_push_button_1.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(REGISTRATION_TYPE_PANEL))
        self.cancel_push_button_2.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(USER_NAME_PANEL))
        self.yes_push_button_2.clicked.connect(lambda: self.set_user_registration_type(True))
        self.no_push_button_2.clicked.connect(lambda: self.set_user_registration_type(False))
        self.cancel_push_button_3.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(REGISTRATION_TYPE_PANEL))
        self.next_push_button_3.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(ID_PRESENT_PANEL))
        self.new_passwd_line_edit.textChanged[str].connect(self.on_passwd_changed)
        self.confirm_passwd_line_edit.textChanged[str].connect(self.on_passwd_changed)
        self.cancel_push_button_4.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(REGISTRATION_TYPE_PANEL))
        self.next_push_button_4.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(ID_PRESENT_PANEL))
        self.old_passwd_line_edit.textChanged.connect(lambda: self.next_push_button_4.setEnabled(bool(self.old_passwd_line_edit.text())))
        self.cancel_push_button_5.clicked.connect(self.set_passwd_panel)
        self.finish_push_button_6.clicked.connect(self.complete_user_registration)
        self.show_passwd_radio_button.clicked.connect(self.toggle_user_passwd_visibility)

    def on_ibutton_presented(self, message):
        """Завершение регистрации пользователя после предъявления идентификатора"""
        self.message = message
        if not self.is_primary_registration:
            # При вторичной регистрации проверить соответствие введенного и предъявленного пароля
            if self.old_passwd_line_edit.text() != self.message["passwd"]:
                dialog = SobolDialog("Ошибка", "Неверный идентификатор или пароль")
                dialog.exec_()
                return
            # Оставить старый пароль
            self.new_passwd_line_edit.setText(self.old_passwd_line_edit.text())
        self.stacked_widget.setCurrentIndex(USER_REGISTERED_PANEL)
        self.finish_push_button_5.setEnabled(True)

    def set_passwd_panel(self):
        """В зависимости от типа регистрации показать соответствующую панель ввода пароля"""
        if self.is_primary_registration:
            self.stacked_widget.setCurrentIndex(NEW_PASSWD_PANEL)
        else:
            self.stacked_widget.setCurrentIndex(OLD_PASSWD_PANEL)

    def complete_user_registration(self):
        """Добавить пользователя"""
        self.userRegistrationСompleted.emit(self.user_name_line_edit.text(), self.new_passwd_line_edit.text(), self.message)

    def cancel_user_registration(self):
        """Отменить регистрацию пользователя"""
        self.userRegistrationСanceled.emit()

    def set_user_registration_type(self, is_primary_registration):
        """Запомнить тип регистрации пользователя и показать следующую панель"""
        self.is_primary_registration = is_primary_registration
        self.set_passwd_panel()

    def on_user_name_changed(self, text: str):
        """Изменить состояние кнопки "Вперед" при вводе имени нового пользователя"""
        self.next_push_button_1.setEnabled(bool(len(text)))

    def on_passwd_changed(self):
        """Изменить состояние кнопки "Вперед" при наличии символов в обоих полях ввода пароля"""
        if len(self.new_passwd_line_edit.text()) != 0 and len(self.confirm_passwd_line_edit.text()) != 0:
            self.next_push_button_3.setEnabled(True)
        else:
            self.next_push_button_3.setEnabled(False)

    def toggle_user_passwd_visibility(self):
        """Переключить видимость пароля пользователя в полях ввода"""
        if self.show_passwd_radio_button.isChecked():
            self.new_passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.confirm_passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.new_passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
            self.confirm_passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)

    def showEvent(self, event: QShowEvent):
        self.stacked_widget.setCurrentIndex(0)
        self.user_name_line_edit.setText("")
        self.new_passwd_line_edit.setText("")
        self.confirm_passwd_line_edit.setText("")
        # Вызывать базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
