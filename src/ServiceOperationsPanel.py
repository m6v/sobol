from PySide2 import QtWidgets

from UiLoader import UiLoader


class ServiceOperationsPanel(QtWidgets.QWidget):

    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/ServiceOperationsPanel.ui", self)
        self.setObjectName("service_operations_panel")
