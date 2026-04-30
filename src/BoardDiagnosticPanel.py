from PySide2 import QtWidgets

from UiLoader import UiLoader


class BoardDiagnosticPanel(QtWidgets.QWidget):

    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/BoardDiagnosticPanel.ui", self)
        self.setObjectName("board_diagnostic_panel")
