from PySide2 import QtWidgets

from UiLoader import UiLoader


class PasswdChangePanel(QtWidgets.QWidget):

    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/PasswdChangePanel.ui", self)
        self.setObjectName("passwd_change_panel")
