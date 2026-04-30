import functools
import logging

from PySide2 import QtWidgets

from Toggle import Toggle
from UiLoader import UiLoader
from AuthenticatorChangePanel import AuthenticatorChangePanel
from BoardDiagnosticPanel import BoardDiagnosticPanel
from CommonParmsPanel import CommonParmsPanel
from IntegrityControlPanel import IntegrityControlPanel
from PasswdChangePanel import PasswdChangePanel
from PasswdParmsPanel import PasswdParmsPanel
from ServiceOperationsPanel import ServiceOperationsPanel
from SysLoadPanel import SysLoadPanel
from UsersListPanel import UsersListPanel
from WorkModePanel import WorkModePanel
from EventsJournalPanel import EventsJournalPanel


class BoardSettingsPage(QtWidgets.QWidget):
    """Страница настроек"""
    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/BoardSettingsPage.ui", self, Toggle)

        self.sys_load_panel = SysLoadPanel(config)
        self.stacked_widget.addWidget(self.sys_load_panel)
        self.work_mode_panel = WorkModePanel(config)
        self.stacked_widget.addWidget(self.work_mode_panel)
        self.users_list_panel = UsersListPanel(config)
        self.stacked_widget.addWidget(self.users_list_panel)
        self.events_journal_panel = EventsJournalPanel(config)
        self.stacked_widget.addWidget(self.events_journal_panel)
        self.common_parms_panel = CommonParmsPanel(config)
        self.stacked_widget.addWidget(self.common_parms_panel)
        self.passwd_parms_panel = PasswdParmsPanel(config)
        self.stacked_widget.addWidget(self.passwd_parms_panel)
        self.integrity_control_panel = IntegrityControlPanel(config)
        self.stacked_widget.addWidget(self.integrity_control_panel)
        self.passwd_change_panel = PasswdChangePanel(config)
        self.stacked_widget.addWidget(self.passwd_change_panel)
        self.authenticator_change_panel = AuthenticatorChangePanel(config)
        self.stacked_widget.addWidget(self.authenticator_change_panel)
        self.board_diagnostic_panel = BoardDiagnosticPanel(config)
        self.stacked_widget.addWidget(self.board_diagnostic_panel)
        self.service_operations_panel = ServiceOperationsPanel(config)
        self.stacked_widget.addWidget(self.service_operations_panel)

        # Перебрать все кнопки в боковой панели и назначить единый обработчик события clicked,
        # передавая ему значение динамического свойства "id"
        for button in self.side_bar_widget.findChildren(QtWidgets.QPushButton):
            button.clicked.connect(functools.partial(self.show_panel, int(button.property("id"))))

    def show_panel(self, id=0):
        self.stacked_widget.setCurrentIndex(id)
        self.updateGeometry()
