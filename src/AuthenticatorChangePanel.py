from PySide2 import QtWidgets

from UiLoader import UiLoader


class AuthenticatorChangePanel(QtWidgets.QWidget):

    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/AuthenticatorChangePanel.ui", self)
        self.setObjectName("authenticator_change_panel")
