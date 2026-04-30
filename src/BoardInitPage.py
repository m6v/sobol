from datetime import datetime
import functools
import logging

from PySide2 import QtWidgets

from Toggle import Toggle
from UiLoader import UiLoader

from AdminRegistrationPage import AdminRegistrationPage
from BoardDiagnosticPanel import BoardDiagnosticPanel
from CommonParmsPanel import CommonParmsPanel
from IntegrityControlPanel import IntegrityControlPanel
from JournalParmsPanel import JournalParmsPanel
from PasswdParmsPanel import PasswdParmsPanel
from ServiceOperationsPanel import ServiceOperationsPanel
from SysLoadPanel import SysLoadPanel


class BoardInitPage(QtWidgets.QWidget):
    """Страница настроек"""
    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/BoardInitPage.ui", self, Toggle)

        self.sys_load_panel = SysLoadPanel(config)
        self.stacked_widget.addWidget(self.sys_load_panel)
        self.common_parms_panel = CommonParmsPanel(config)
        self.stacked_widget.addWidget(self.common_parms_panel)
        self.journal_parms_panel = JournalParmsPanel(config)
        self.stacked_widget.addWidget(self.journal_parms_panel)
        self.passwd_parms_panel = PasswdParmsPanel(config)
        self.stacked_widget.addWidget(self.passwd_parms_panel)
        # В промежутке между этими панелями вызов мастера регистрации администратора
        self.integrity_control_panel = IntegrityControlPanel(config)
        self.stacked_widget.addWidget(self.integrity_control_panel)
        self.board_diagnostic_panel = BoardDiagnosticPanel(config)
        self.stacked_widget.addWidget(self.board_diagnostic_panel)
        self.service_operations_panel = ServiceOperationsPanel(config)
        self.stacked_widget.addWidget(self.service_operations_panel)

        # Перебрать все кнопки в боковой панели и назначить единый обработчик события clicked,
        # передавая ему значение динамического свойства "id"
        for button in self.side_bar_widget.findChildren(QtWidgets.QPushButton):
            button.clicked.connect(functools.partial(self.show_panel, int(button.property("id"))))

    def show_panel(self, index=0):
        self.stacked_widget.setCurrentIndex(index)
        # Показывать метки шагов только с панелью инициализации платы
        if index:
            self.labels_widget.hide()
        else:
            self.labels_widget.show()
        self.updateGeometry()

    def show_init_panel(self, index: int):
        """Показать выбранную панель инициализации с сохраненными настройками"""
        self.admin_actions_panel.stacked_widget.setCurrentIndex(0)
        self.init_panel.stacked_widget.setCurrentIndex(index)

        # Подсветить метку, соответствующую текущему шагу (index) инициализации
        for i in range(self.init_panel.horizontal_layout.count()):
            item = self.init_panel.horizontal_layout.itemAt(i).widget()
            if i == index:
                item.setStyleSheet("""
                    background-color: #48A23F;
                    color: white;
                """)
            else:
                item.setStyleSheet("""
                    background-color: white;
                    color: black;
                """)
        # Уточнить в поле с временем и датой необходимо выполнять динамическое обновление
        # или достаточно выставить текущее время при открытии панели
        if not index:
            self.sys_parms_panel.sys_datetime_line_edit.setText(datetime.now().strftime("%H:%M %d/%m/%Y"))
