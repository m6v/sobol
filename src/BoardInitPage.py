from datetime import datetime
import functools
import logging

from PySide2 import QtCore, QtWidgets

import constants
from Toggle import Toggle
from UiLoader import UiLoader

from AdminRegistrationPanel import AdminRegistrationPanel
from BoardDiagnosticPanel import BoardDiagnosticPanel
from CommonParmsPanel import CommonParmsPanel
from IntegrityControlPanel import IntegrityControlPanel
from JournalParmsPanel import JournalParmsPanel
from PasswdParmsPanel import PasswdParmsPanel
from ServiceOperationsPanel import ServiceOperationsPanel
from SysLoadPanel import SysLoadPanel


class BoardInitPage(QtWidgets.QWidget):
    """Страница инициализации платы"""
    adminRegistrationRequested = QtCore.Signal(bool)

    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/BoardInitPage.ui", self, Toggle)

        self.sys_load_panel = SysLoadPanel(config)
        self.sys_load_panel.save_push_button.setText("Вперед")
        self.sys_load_panel.save_push_button.clicked.connect(lambda: self.show_init_panel(constants.COMMON_PARMS_PANEL))
        self.sys_load_panel.sys_load_push_button.hide()
        self.stacked_widget.addWidget(self.sys_load_panel)

        self.common_parms_panel = CommonParmsPanel(config)
        self.common_parms_panel.save_push_button.setText("Вперед")
        self.common_parms_panel.cancel_push_button.setText("Назад")
        self.common_parms_panel.save_push_button.clicked.connect(lambda: self.show_init_panel(constants.JOURNAL_PARMS_PANEL))
        self.common_parms_panel.cancel_push_button.clicked.connect(lambda: self.show_init_panel(constants.SYS_LOAD_PANEL))
        self.stacked_widget.addWidget(self.common_parms_panel)

        self.journal_parms_panel = JournalParmsPanel(config)
        self.journal_parms_panel.save_push_button.setText("Вперед")
        self.journal_parms_panel.cancel_push_button.setText("Назад")
        self.journal_parms_panel.save_push_button.clicked.connect(lambda: self.show_init_panel(constants.PASSWD_PARMS_PANEL))
        self.journal_parms_panel.cancel_push_button.clicked.connect(lambda: self.show_init_panel(constants.COMMON_PARMS_PANEL))
        self.stacked_widget.addWidget(self.journal_parms_panel)

        self.passwd_parms_panel = PasswdParmsPanel(config)
        self.passwd_parms_panel.save_push_button.setText("Вперед")
        self.passwd_parms_panel.cancel_push_button.setText("Назад")
        self.passwd_parms_panel.save_push_button.clicked.connect(lambda: self.show_init_panel(constants.ADMIN_REGISTRATION_PANEL))
        self.passwd_parms_panel.cancel_push_button.clicked.connect(lambda: self.show_init_panel(constants.JOURNAL_PARMS_PANEL))
        self.stacked_widget.addWidget(self.passwd_parms_panel)

        self.admin_registration_panel = AdminRegistrationPanel(config)
        # Запрос первичной или вторичной регистрации администратора
        self.admin_registration_panel.yes_push_button.clicked.connect(lambda: self.request_admin_registration(True))
        self.admin_registration_panel.no_push_button.clicked.connect(lambda: self.request_admin_registration(False))
        self.admin_registration_panel.cancel_push_button.clicked.connect(lambda: self.show_init_panel(constants.PASSWD_PARMS_PANEL))

        self.stacked_widget.addWidget(self.admin_registration_panel)

        self.integrity_control_panel = IntegrityControlPanel(config)
        self.integrity_control_panel.save_push_button.setText("Вперед")
        self.integrity_control_panel.cancel_push_button.hide()
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
        # Подсветить метку, соответствующую текущему шагу (index) инициализации
        for i in range(self.horizontal_layout.count()):
            item = self.horizontal_layout.itemAt(i).widget()
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

        self.stacked_widget.setCurrentIndex(0)
        self.stacked_widget.setCurrentIndex(index)

        # TODO следующие команды переместить в MainWidget
        # Уточнить в поле с временем и датой необходимо выполнять динамическое обновление
        # или достаточно выставить текущее время при открытии панели
        # if not index:
        #     self.sys_parms_panel.sys_datetime_line_edit.setText(datetime.now().strftime("%H:%M %d/%m/%Y"))

    def request_admin_registration(self, is_primary_admin_registration):
        """Запросить вызов мастера регистрации администратора"""
        self.show_init_panel(constants.INTEGRITY_CONTROL_PANEL)
        self.adminRegistrationRequested.emit(is_primary_admin_registration)
