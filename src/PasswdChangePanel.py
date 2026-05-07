from PySide2 import QtCore, QtWidgets

from UiLoader import UiLoader


class PasswdChangePanel(QtWidgets.QWidget):
    """Панель с кнопкой вызова мастера смены пароля администратора"""
    adminPasswdChangeRequested = QtCore.Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/PasswdChangePanel.ui", self)
        self.setObjectName("passwd_change_panel")

        self.change_passwd_push_button.clicked.connect(self.adminPasswdChangeRequested)
