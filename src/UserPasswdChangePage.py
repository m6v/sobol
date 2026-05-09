from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QShowEvent

from config import config
from UiLoader import UiLoader
from SobolDialog import SobolDialog

OLD_PASSWD_ENTRY_PAGE = 0
NEW_PASSWD_ENTRY_PAGE = 1
WAIT_ID_PAGE = 2
COMPLETION_PAGE = 3


class UserPasswdChangePage(QtWidgets.QWidget):
    """Страница смены пароля пользователя"""
    userPasswdChangeCompleted = QtCore.Signal(str, str, dict)
    userPasswdChangeCanceled = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/UserPasswdChangePage.ui", self)

        self.old_passwd_line_edit.textChanged[str].connect(self.on_old_passwd_changed)
        self.new_passwd_line_edit.textChanged[str].connect(self.on_new_passwd_changed)
        self.confirm_passwd_line_edit.textChanged[str].connect(self.on_new_passwd_changed)
        self.next_push_button_1.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(NEW_PASSWD_ENTRY_PAGE))
        self.cancel_push_button_1.clicked.connect(self.userPasswdChangeCanceled.emit)
        self.next_push_button_2.clicked.connect(self.check_passwd)
        self.cancel_push_button_2.clicked.connect(self.userPasswdChangeCanceled.emit)
        self.cancel_push_button_3.clicked.connect(self.userPasswdChangeCanceled.emit)
        self.finish_push_button_4.clicked.connect(self.userPasswdChangeCanceled.emit)

    def on_old_passwd_changed(self, old_passwd):
        if old_passwd:
            self.next_push_button_1.setEnabled(True)
        else:
            self.next_push_button_1.setEnabled(False)

    def check_passwd(self):
        """Проверить совпадение пароля в обоих полях ввода и его соответствие требованиям сложности"""
        if self.new_passwd_line_edit.text() != self.confirm_passwd_line_edit.text():
            dialog = SobolDialog("Ошибка", "Введенные пароли не совпадают, повторите ввод!")
            dialog.exec_()
            return
        self.stacked_widget.setCurrentIndex(WAIT_ID_PAGE)

    def on_new_passwd_changed(self):
        """Изменить состояние кнопки "Вперед" при наличии символов в обоих полях ввода пароля"""
        if len(self.new_passwd_line_edit.text()) != 0 and len(self.confirm_passwd_line_edit.text()) != 0:
            self.next_push_button_2.setEnabled(True)
        else:
            self.next_push_button_2.setEnabled(False)

    def on_ibutton_presented(self, message):
        # Сохранить идентификатор предъявленной ibutton
        if self.old_passwd_line_edit.text() != message["passwd"]:
            dialog = SobolDialog("Ошибка", "Неверный идентификатор или пароль!")
            dialog.exec_()
            return
        self.userPasswdChangeCompleted.emit(message["user_name"], self.new_passwd_line_edit.text(), message)
        self.stacked_widget.setCurrentIndex(COMPLETION_PAGE)
        self.finish_push_button_4.setEnabled(True)

    def showEvent(self, event: QShowEvent):
        self.stacked_widget.setCurrentIndex(0)
        # Очистить все элементы ввода от предыдущих итераций
        self.old_passwd_line_edit.setText("")
        self.new_passwd_line_edit.setText("")
        self.confirm_passwd_line_edit.setText("")
        # Вызывать базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
