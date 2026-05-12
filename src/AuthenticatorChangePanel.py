from PySide2 import QtCore, QtWidgets

from UiLoader import UiLoader


class AuthenticatorChangePanel(QtWidgets.QWidget):
    """Панель с кнопкой вызова мастера смены аутентификатора администратора"""
    adminAutenticatorChangeRequested = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/AuthenticatorChangePanel.ui", self)
        self.setObjectName("authenticator_change_panel")

        self.change_auth_push_button.clicked.connect(self.adminAutenticatorChangeRequested)
