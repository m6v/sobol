import logging

from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QShowEvent

from UiLoader import UiLoader
from SobolDialog import SobolDialog

PASSWD_ENTRY_PAGE = 0
WAIT_ID_PAGE = 1
COMPLETION_PAGE = 2


class AdminAuthenticatorChangePage(QtWidgets.QWidget):
    """Страница смены пароля пользователя"""
    adminAuthenticatorChangeCompleted = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/AdminAuthenticatorChangePage.ui", self)

        self.passwd_line_edit.textChanged[str].connect(self.on_passwd_changed)
        self.next_push_button_1.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(WAIT_ID_PAGE))
        self.cancel_push_button_1.clicked.connect(self.adminAuthenticatorChangeCompleted.emit)
        self.next_push_button_2.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(COMPLETION_PAGE))
        self.cancel_push_button_2.clicked.connect(self.adminAuthenticatorChangeCompleted.emit)
        self.yes_push_button_3.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(WAIT_ID_PAGE))
        self.no_push_button_3.clicked.connect(self.adminAuthenticatorChangeCompleted.emit)

    def on_passwd_changed(self, passwd):
        if passwd:
            self.next_push_button_1.setEnabled(True)
        else:
            self.next_push_button_1.setEnabled(False)

    def on_ibutton_presented(self, message):
        # Сохранить идентификатор предъявленной ibutton
        self.message = message
        logging.debug(message)
        # Проверить правильность старого пароля
        if self.passwd_line_edit.text() != message["passwd"]:
            dialog = SobolDialog("Ошибка", "Неверный идентификатор или пароль!")
            dialog.exec_()
            return
        # В имитаторе аутентификаторы не используются, поэтому просто переходим дальше
        self.stacked_widget.setCurrentIndex(COMPLETION_PAGE)

    def showEvent(self, event: QShowEvent):
        self.stacked_widget.setCurrentIndex(PASSWD_ENTRY_PAGE)
        self.passwd_line_edit.setText("")
        # Вызвать базовый класс, чтобы не нарушить цепочку Qt
        super().showEvent(event)
