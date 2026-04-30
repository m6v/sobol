import logging

from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QShowEvent

from UiLoader import UiLoader


class UserRegistrationPage(QtWidgets.QWidget):
    """Страница регистрации пользователя"""
    registrationСompleted = QtCore.Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/UserRegistrationPage.ui", self)

        self.user_name.textChanged[str].connect(self.user_name_changed)
        self.next_push_button_1.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.yes_push_button_2.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.next_push_button_3.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        self.passwd_line_edit.textChanged[str].connect(self.passwd_changed)
        self.passwd_confirm_line_edit.textChanged[str].connect(self.passwd_changed)
        self.finish_push_button_4.clicked.connect(self.finish_registration)

    def on_ibutton_presented(self, message):
        # TODO здесь нужно сохранить идентификатор предъявленной ibutton
        self.finish_push_button_4.setEnabled(True)

    def finish_registration(self):
        # TODO Здесь нужно либо сохранить учетку, либо подать сигнал о сохранении
        self.registrationСompleted.emit()

    def user_name_changed(self, text: str):
        """Изменить состояние кнопки "Вперед" при вводе имени нового пользователя"""
        self.next_push_button_1.setEnabled(bool(len(text)))

    def passwd_changed(self):
        """Изменить состояние кнопки "Вперед" при наличии символов в обоих полях ввода пароля"""
        if len(self.passwd_line_edit.text()) != 0 and len(self.passwd_confirm_line_edit.text()) != 0:
            self.next_push_button_3.setEnabled(True)
        else:
            self.next_push_button_3.setEnabled(False)

    def showEvent(self, event: QShowEvent):
        self.stacked_widget.setCurrentIndex(0)
        # TODO Далее нужно очистить все элементы ввода от предыдущих итераций
        # Обязательно вызываем базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
