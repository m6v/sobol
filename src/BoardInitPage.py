from PySide2 import QtCore, QtWidgets

from Toggle import Toggle
from UiLoader import UiLoader
from SobolDialog import SobolDialog

from AdminRegistrationPanel import AdminRegistrationPanel
from BoardDiagnosticPanel import BoardDiagnosticPanel
from CommonParmsPanel import CommonParmsPanel
from IntegrityControlPanel import IntegrityControlPanel
from JournalParmsPanel import JournalParmsPanel
from PasswdParmsPanel import PasswdParmsPanel
from ServiceOperationsPanel import ServiceOperationsPanel
from SysLoadPanel import SysLoadPanel

SYS_LOAD_PANEL = 0
COMMON_PARMS_PANEL = 1
JOURNAL_PARMS_PANEL = 2
PASSWD_PARMS_PANEL = 3
ADMIN_REGISTRATION_PANEL = 4
INTEGRITY_CONTROL_PANEL = 5
BOARD_DIAGNOSTIC_PANEL = 6
SEVICE_OPERATIONS_PANEL = 7


class BoardInitPage(QtWidgets.QWidget):
    """Страница инициализации платы"""
    adminRegistrationRequested = QtCore.Signal(bool)
    boardInitCompleted = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/BoardInitPage.ui", self, Toggle)

        # Это панель инициализации платы, но использует тот же класс,
        # что и панель с параметрами загрузки ОС в режиме "Работа"
        self.sys_load_panel = SysLoadPanel()
        self.sys_load_panel.save_push_button.setText("Вперед")
        self.sys_load_panel.save_push_button.clicked.connect(lambda: self.show_init_panel(COMMON_PARMS_PANEL))
        self.sys_load_panel.sys_load_push_button.hide()
        self.stacked_widget.addWidget(self.sys_load_panel)

        self.common_parms_panel = CommonParmsPanel()
        self.common_parms_panel.save_push_button.setText("Вперед")
        self.common_parms_panel.cancel_push_button.setText("Назад")
        self.common_parms_panel.save_push_button.clicked.connect(lambda: self.show_init_panel(JOURNAL_PARMS_PANEL))
        self.common_parms_panel.cancel_push_button.clicked.connect(lambda: self.show_init_panel(SYS_LOAD_PANEL))
        self.stacked_widget.addWidget(self.common_parms_panel)

        self.journal_parms_panel = JournalParmsPanel()
        self.journal_parms_panel.save_push_button.setText("Вперед")
        self.journal_parms_panel.cancel_push_button.setText("Назад")
        self.journal_parms_panel.save_push_button.clicked.connect(lambda: self.show_init_panel(PASSWD_PARMS_PANEL))
        self.journal_parms_panel.cancel_push_button.clicked.connect(lambda: self.show_init_panel(COMMON_PARMS_PANEL))
        self.stacked_widget.addWidget(self.journal_parms_panel)

        self.passwd_parms_panel = PasswdParmsPanel()
        self.passwd_parms_panel.save_push_button.setText("Вперед")
        self.passwd_parms_panel.cancel_push_button.setText("Назад")
        self.passwd_parms_panel.save_push_button.clicked.connect(lambda: self.show_init_panel(ADMIN_REGISTRATION_PANEL))
        self.passwd_parms_panel.cancel_push_button.clicked.connect(lambda: self.show_init_panel(JOURNAL_PARMS_PANEL))
        self.stacked_widget.addWidget(self.passwd_parms_panel)

        self.admin_registration_panel = AdminRegistrationPanel()
        # Запрос первичной регистрации администратора
        self.admin_registration_panel.yes_push_button.clicked.connect(lambda: self.request_admin_registration(True))
        # Запрос вторичной регистрации администратора
        self.admin_registration_panel.no_push_button.clicked.connect(lambda: self.request_admin_registration(False))
        # Отмена регистрации администратора
        self.admin_registration_panel.cancel_push_button.clicked.connect(lambda: self.show_init_panel(PASSWD_PARMS_PANEL))
        self.stacked_widget.addWidget(self.admin_registration_panel)

        self.integrity_control_panel = IntegrityControlPanel()
        self.integrity_control_panel.save_push_button.setText("Вперед")
        self.integrity_control_panel.cancel_push_button.hide()
        self.integrity_control_panel.save_push_button.clicked.connect(self.complete_board_init)
        self.stacked_widget.addWidget(self.integrity_control_panel)

        self.board_diagnostic_panel = BoardDiagnosticPanel()
        self.stacked_widget.addWidget(self.board_diagnostic_panel)

        self.service_operations_panel = ServiceOperationsPanel()
        self.stacked_widget.addWidget(self.service_operations_panel)

        self.board_init_push_button.clicked.connect(lambda: self.show_panel(SYS_LOAD_PANEL))
        self.board_diagnostic_push_button.clicked.connect(lambda: self.show_panel(BOARD_DIAGNOSTIC_PANEL))
        self.service_operations_push_button.clicked.connect(lambda: self.show_panel(SEVICE_OPERATIONS_PANEL))

        self.show_panel(SYS_LOAD_PANEL)

    def show_panel(self, index=0):
        self.stacked_widget.setCurrentIndex(index)
        # Показывать метки шагов только с панелью инициализации платы
        if index:
            self.labels_widget.hide()
        else:
            self.labels_widget.show()
            self.show_init_panel(0)
        self.updateGeometry()

    def show_init_panel(self, index=0):
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

    def request_admin_registration(self, is_primary_admin_registration):
        """Запросить вызов мастера регистрации администратора"""
        self.adminRegistrationRequested.emit(is_primary_admin_registration)
        self.show_init_panel(INTEGRITY_CONTROL_PANEL)

    def complete_board_init(self):
        """Завершить инициализацию платы"""
        dialog = SobolDialog("Внимание", "Инициализация платы завершена. Компьютер будет перезагружен")
        dialog.exec_()
        self.boardInitCompleted.emit()
