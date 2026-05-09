import logging

from PySide2 import QtWidgets

from UiLoader import UiLoader


class AdminRegistrationPanel(QtWidgets.QWidget):
    """Страница регистрации администратора"""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/AdminRegistrationPanel.ui", self)
