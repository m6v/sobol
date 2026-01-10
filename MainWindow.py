import configparser
import datetime
import functools
import inspect
import libvirt
import logging
import os
import secrets
import string
import subprocess
import sys

from typing import Dict

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtWidgets import QLineEdit, QCheckBox, QComboBox
from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

import dbus
import dbus.mainloop.glib
import pyudev

from constants import VIR_DOMAIN_EVENT_MAPPING, VIR_DOMAIN_STATE_MAPPING
from BackgroundedWidget import BackgroundedWidget
from UiLoader import UiLoader
from toggle import Toggle

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()

INITIAL_DIR = CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
# Если установлена переменная окружения _MEIPASS, программа запущена
# из временного каталога, созданного при распаковке бандла
if hasattr(sys, "_MEIPASS"):
    # Путь к временному каталогу взять из sys.executable
    INITIAL_DIR = os.path.dirname(sys.executable)

# Для логирования в файл, добавить filename="app.log" иначе лог в консоль
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

# Индексы панелей
WAIT_ID_PAGE = 0
PASSWD_PAGE = 1
ADMIN_CHOICE_PAGE = 2
USER_CHOICE_PAGE = 3
SETTINGS_PAGE = 4
WEB_VIEW_PAGE = 5


def str2bool(s):
    """Преобразовать строковое предстваление истины в boolean"""
    return s.lower() in ("y", "yes", "true", "д", "да", "1")


def gen_password(length=8):
    if length < 4:
        raise ValueError("Length must be >= 4")

    chars = {
        "lower": string.ascii_lowercase,
        "upper": string.ascii_uppercase,
        "digit": string.digits,
        "symbol": string.punctuation
    }

    password = [
        secrets.choice(chars["lower"]),
        secrets.choice(chars["upper"]),
        secrets.choice(chars["digit"]),
        secrets.choice(chars["symbol"]),
    ]

    all_chars = ''.join(chars.values())
    password += [secrets.choice(all_chars) for _ in range(length - 4)]
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


class WebEnginePage(QWebEnginePage):
    navigation_request = QtCore.Signal(str)

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        # Если переходить по ссылке не требуется, возвратить False, иначе True
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            logging.debug(url.path())
            self.navigation_request.emit(url.path())
            # Здесь можно анализировать url и в зависимости от него
            # разрешать или запрещать переход по ссылке
            return False
        return True


class CustomWebEngineView(QWebEngineView):
    def __init__(self, *args, **kwargs):
        QWebEngineView.__init__(self, *args, **kwargs)
        self.setPage(WebEnginePage(self))


class SobolDialog(QtWidgets.QDialog):
    def __init__(self, text, caption="Внимание"):
        super().__init__()

        self.loader = UiLoader()
        self.loader.loadUi("SobolDialog.ui", self)

        # NB! Геометрия кнопок почему-то не устанавливается?!
        dialog_style_sheet = """
            QWidget {
                font: 9pt "Monospace Regular";
                background-color: #F5F5F5;
            }
            QPushButton {
                background-color: #48A23F;
                width: 120px;
                height: 48px;
                color: white;
           }
           QPushButton:hover {
                background: #3D8A36;
           }
           QPushButton:pressed {
                background-color: #3D8A36;
           }
        """
        self.setStyleSheet(dialog_style_sheet)
        self.caption_label.setText(caption)
        self.text_label.setText(text)

        self.yes_push_button.clicked.connect(self.accept)
        self.no_push_button.clicked.connect(self.reject)


class MainWindow(QtWidgets.QMainWindow):
    # Сигнал "предъявления" iButton
    ibutton_present = QtCore.Signal(dict)

    def __init__(self, config_file):
        super().__init__()

        self.loader = UiLoader()
        self.loader.registerCustomWidget(BackgroundedWidget)
        self.loader.registerCustomWidget(Toggle)
        self.loader.registerCustomWidget(QWebEngineView)
        self.loader.loadUi("MainWindow.ui", self)
        # Если config_file отсутствует, добавить к нему текущий путь в надежде, что найдется там
        # TODO Сделать проверку наличия конфига, иначе дальше вываливаемся с неочевидным исключением
        if not os.path.isfile(config_file):
            config_file = os.path.join(INITIAL_DIR, config_file)
        self.config_file = os.path.join(INITIAL_DIR, config_file)
        self.config = configparser.ConfigParser(allow_no_value=True)
        # Установить чувствительность ключей к регистру
        self.config.optionxform = str
        self.config.read(self.config_file)
        try:
            # Список с параметрами зарегистрированных пользователей (идентификатор iButton, имя и др.)
            self.users = eval(self.config.get("general", "users"))
            # Список с идентификаторами iButton зарегистрированных администраторов
            self.admins = eval(self.config.get("general", "admins"))
            # Суммарное кол-во неудачных попыток входа (с момента инициализации)
            self.failed_logins = int(self.config.get("general", "failed_logins"))
            # Имя виртуальной машины
            self.domain_name = self.config.get("general", "domain_name")

            self.setWindowTitle(self.config.get("window", "title"))
            # Разбить строку на элементы, преобразовать их в целые числа и получить QRect с геометрией главного окна
            geometry = QtCore.QRect(*map(int, self.config.get("window", "geometry").split(";")))
            # Восстановить геометрию и состояние главного окна
            self.setGeometry(geometry)
            state = int(self.config.get("window", "state"))
            self.restoreState(bytearray(state))
        except configparser.NoOptionError as e:
            logging.warning(e)
        except configparser.NoSectionError as e:
            logging.error(e)

        # Прочитать имя и uuid загрузочного раздела
        context = pyudev.Context()
        for device in context.list_devices(subsystem="block", DEVTYPE="partition"):
           if device.get("ID_PART_ENTRY_FLAGS"):
               logging.debug(device.device_node)
               bootable_partition = device.device_node
               bootable_uuid = device.get("ID_FS_UUID")
        # logging.debug(subprocess.check_output(["efibootmgr"], text=True).split("\n"))

        try:
            # Register the default event implementation
            libvirt.virEventRegisterDefaultImpl()
            # Открыть соединение с локальным гипервизором
            conn = libvirt.open(None)
            self.dom = conn.lookupByName(self.domain_name)
            # state - состояние виртуальной машины (число из перечисления virDomainState)
            # reason - причина перехода в определённое состояние (число из перечисления virDomain*Reason)
            state, reason = self.dom.state()
            logging.info(f"Domain {self.dom.name()}, state: {VIR_DOMAIN_STATE_MAPPING.get(state)}, reason: {reason}")
            """
            if state == libvirt.VIR_DOMAIN_RUNNING:
                # Если клиент vnc или spice будет отображаться в имитаторе,
                # установить здесь его в качестве первой открывающейся панели
                pass
            """
        except libvirt.libvirtError as e:
            logging.error(e)

        self.web_engine_view = QWebEngineView()
        self.main_stacked_widget.addWidget(self.web_engine_view)

        # Создать боковую панель (sidebar)
        self.settings_sidebar_widget = QtWidgets.QWidget()
        # Установить фиксированную ширину боковой панели
        self.settings_sidebar_widget.setFixedWidth(230)
        self.settings_sidebar_widget.setContentsMargins(0, 0, 0, 0)

        sidebar_style_sheet = """
            QWidget {
                font: 9pt "Monospace Regular";
                background-image: url(sidebar.png);
                background-repeat: no-repeat;
                background-position: up;
                background-color: #48A23F;
            }
            QPushButton {
                background-color: #48A23F;
                width: 75px ;
                height: 47px;
                border: none;
                text-align: left;
                padding: 0px 0px 0px 10px;
                color: white;
           }
           QPushButton:hover {
                background: #3D8A36;
           }
           QPushButton:pressed {
                background-color: #3D8A36;
           }
        """

        # Настроить параметры отображения боковой панели страницы настроек
        self.settings_sidebar_widget.setStyleSheet(sidebar_style_sheet)

        # Создать менеджер компоновки с кнопками меню
        settings_sidebar_layout = QtWidgets.QVBoxLayout(self.settings_sidebar_widget)
        settings_sidebar_layout.setContentsMargins(0, 0, 0, 0)
        settings_sidebar_layout.setSpacing(0)

        # Если зарегистрирован хоть один администратор, считаем, что комплекс инициализирован
        if self.admins:
            self.buttons = {
                "Загрузка ОС": "icons/sys_load.png",
                "Режим работы": "icons/work_mode.png",
                "Список пользователей": "icons/users_list.png",
                "Журнал событий": "icons/journal.png",
                "Общие параметры": "icons/common_parms.png",
                "Параметры паролей": "icons/passwd_parms.png",
                "Контроль целостности": "icons/integrity_control.png",
                "Смена пароля": "icons/passwd_change.png",
                "Смена аутентификатора": "icons/user_id_change.png",
                "Диагностика платы": "icons/diagnostic.png",
                "Служебные операции": "icons/service_operations.png"
            }
            self.settings_panels = {
                "sys_load_panel": "panels/SysLoadPanel.ui",
                "work_mode_panel": "panels/WorkModePanel.ui",
                "user_list_panel": "panels/UserListPanel.ui",
                "event_journal_panel": "panels/JournalPanel.ui",
                "common_parms_panel": "panels/CommonParmsPanel.ui",
                "passwd_parms_panel": "panels/PasswdParmsPanel.ui",
                "integrity_control_panel": "panels/IntegrityControlPanel.ui",
                "passwd_change_panel": "panels/PasswdChangePanel.ui",
                "id_change_panel": "panels/IdChangePanel.ui",
                "diagnostic_panel": "panels/DiagnosticPanel.ui",
                "service_operations_panel": "panels/ServiceOperationsPanel.ui",
                "user_actions_panel": "panels/UserActionsPanel.ui"
            }
        else:
            self.buttons = {
                "Инициализация платы": "icons/sys_load.png",
                "Диагностика платы": "icons/diagnostic.png",
                "Служебные операции": "icons/service_operations.png"
            }
            self.settings_panels = {
                "init_panel": "panels/InitPanel.ui",
                "diagnostic_panel": "panels/DiagnosticPanel.ui",
                "service_operations_panel": "panels/ServiceOperationsPanel.ui",
            }

        verticalSpacer = QtWidgets.QSpacerItem(20, 15, QtWidgets.QSizePolicy.Fixed)
        settings_sidebar_layout.addItem(verticalSpacer)
        for i, item in enumerate(self.buttons.items()):
            button = QtWidgets.QPushButton(item[0])
            button.setIcon(QtGui.QIcon(item[1]))
            settings_sidebar_layout.addWidget(button)
            # Связать событие нажания кнопки с обработчиком, передавая в обработчик номер кнопки
            button.clicked.connect(functools.partial(self.show_main_panel, i))
        verticalSpacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        settings_sidebar_layout.addItem(verticalSpacer)
        # Вставить созданный менеджер компоновки в нулевую позицию менеджера компоновки главного окна (settings_horizontal_layout)
        self.settings_horizontal_layout.insertWidget(0, self.settings_sidebar_widget, alignment=QtCore.Qt.AlignLeft)
        # Динамически добавить панели в стек виджетов, с последующим обращением к ним self.sys_load_panel и т.д.
        for panel_name, ui_file in self.settings_panels.items():
            panel = self.loader.loadUi(os.path.join(CURRENT_DIR, ui_file))
            panel.setObjectName(panel_name)
            setattr(self, panel_name, panel)
            self.settings_stacked_widget.addWidget(getattr(self, panel_name))

        if self.admins:
            # При запуске открыть панель WAIT_ID_PAGE
            self.show_main_panel(WAIT_ID_PAGE)

            self.show_journal_panel(0)

            self.sys_load_panel.save_push_button.clicked.connect(functools.partial(self.save_panel_settings, self.sys_load_panel))

            self.integrity_control_panel.save_push_button.clicked.connect(functools.partial(self.save_panel_settings, self.integrity_control_panel))

            self.user_actions_panel.cancel_push_button_1.clicked.connect(self.close_user_ctl_wizard)
            self.user_actions_panel.cancel_push_button_2.clicked.connect(self.close_user_ctl_wizard)
            self.user_actions_panel.cancel_push_button_3.clicked.connect(self.close_user_ctl_wizard)
            self.user_actions_panel.cancel_push_button_4.clicked.connect(self.close_user_ctl_wizard)
            self.user_actions_panel.cancel_push_button_5.clicked.connect(self.close_user_ctl_wizard)
            self.user_actions_panel.cancel_push_button_6.clicked.connect(self.close_user_ctl_wizard)
            self.user_actions_panel.cancel_push_button_7.clicked.connect(self.close_user_ctl_wizard)
            self.user_actions_panel.finish_push_button_4.clicked.connect(self.close_user_ctl_wizard)
            self.user_actions_panel.finish_push_button_8.clicked.connect(self.close_user_ctl_wizard)

            self.user_actions_panel.user_name.textChanged[str].connect(self.user_name_changed)
            self.user_actions_panel.next_push_button_1.clicked.connect(self.check_user_name)
            self.user_actions_panel.yes_push_button_2.clicked.connect(self.next_user_action_panel)
            self.user_actions_panel.passwd_line_edit.textChanged[str].connect(self.user_passwd_changed)
            self.user_actions_panel.passwd_confirm_line_edit.textChanged[str].connect(self.user_passwd_changed)
            self.user_actions_panel.next_push_button_3.clicked.connect(self.check_user_passwd)
            self.user_actions_panel.passwd_gen_push_button.clicked.connect(self.gen_user_passwd)
            self.user_actions_panel.show_passwd_radio_button.clicked.connect(self.toggle_user_passwd_visibility)

            self.event_journal_panel.view_journal_push_button.clicked.connect(functools.partial(self.show_journal_panel, 0))
            self.event_journal_panel.export_journal_push_button.clicked.connect(functools.partial(self.show_journal_panel, 1))
            self.event_journal_panel.parms_journal_push_button.clicked.connect(functools.partial(self.show_journal_panel, 2))
            self.event_journal_panel.search_journal_push_button.clicked.connect(functools.partial(self.show_journal_panel, 3))
            self.event_journal_panel.select_parms_push_button.clicked.connect(functools.partial(self.show_journal_panel, 0))
            self.event_journal_panel.cancel_parms_push_button.clicked.connect(functools.partial(self.show_journal_panel, 0))
            self.event_journal_panel.select_all_push_button.clicked.connect(self.event_journal_panel.events_type_list_widget.selectAll)
            self.event_journal_panel.clear_all_push_button.clicked.connect(self.event_journal_panel.events_type_list_widget.clearSelection)
            self.event_journal_panel.save_push_button.clicked.connect(functools.partial(self.save_panel_settings, self.event_journal_panel))
            self.event_journal_panel.events_type_search_check_box.clicked.connect(self.trigger_events_type_search)
            self.event_journal_panel.events_time_search_check_box.clicked.connect(self.trigger_events_time_search)

            self.update_user_list_panel()

            # Установка свойства в ui почему-то не работает, делаем здесь
            self.passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)

            # Связать сигнал и слоты
            self.enter_push_button.clicked.connect(self.auth_user)
            self.passwd_line_edit.returnPressed.connect(self.auth_user)
            # Чтобы не писать отдельный обработчик вызываем метод setCurrentIndex с передачей ему номера панели
            self.go_settings_push_button.clicked.connect(functools.partial(self.main_stacked_widget.setCurrentIndex, SETTINGS_PAGE))
            # Вызов метода запуска виртуальной машины
            self.sys_load_push_button.clicked.connect(self.sys_load)
            self.sys_load_panel.sys_load_push_button.clicked.connect(self.sys_load)

            self.user_list_panel.add_user_push_button.clicked.connect(self.show_user_creation_wizard)
            self.user_list_panel.del_user_push_button.clicked.connect(self.del_user)
            self.user_list_panel.del_all_users_push_button.clicked.connect(self.del_all_users)
            self.user_list_panel.user_list_widget.itemClicked.connect(self.show_user_parms)
            self.user_list_panel.user_list_widget.itemActivated.connect(self.show_user_parms)
            self.user_list_panel.save_push_button.clicked.connect(self.save_user_parms)
            self.user_list_panel.show_passwd_radio_button.clicked.connect(self.toggle_user_passwd_visibility)

            self.timer = QtCore.QTimer()
            # Время до входа в систему, отображаемое в первых двух окнах
            self.remaining_time = int(self.config.get("common_parms_panel", "time_limit_line_edit")) * 60
            # Если 0, то не обрабатывать таймаут
            if self.remaining_time:
                self.timer.timeout.connect(self.decrease_remaining_time)

            # Запустить таймер ожидания чтения идентификатора iButton
            self.ibutton_present[dict].connect(self.read_ibutton)
            self.timer.start(1000)
            # Открыть страницу ожидания предъявления идентификатора
            self.main_stacked_widget.setCurrentIndex(WAIT_ID_PAGE)
        else:
            # Открыть страницу инициализации
            self.main_stacked_widget.setCurrentIndex(SETTINGS_PAGE)

            self.init_panels = {
                "sys_parms_panel": "panels/SysParmsPanel.ui",
                "common_parms_panel": "panels/CommonParmsPanel.ui",
                "journal_parms_panel": "panels/JournalParms.ui",
                "passwd_parms_panel": "panels/PasswdParmsPanel.ui",
                "admin_actions_panel": "panels/AdminActionsPanel.ui",
                "integrity_control_panel": "panels/IntegrityControlPanel.ui"
            }
            for panel_name, ui_file in self.init_panels.items():
                panel = self.loader.loadUi(os.path.join(CURRENT_DIR, ui_file))
                panel.setObjectName(panel_name)
                setattr(self, panel_name, panel)
                self.init_panel.stacked_widget.addWidget(getattr(self, panel_name))

            # Настроить таблицу со списком операций при регистрации администратора
            self.admin_actions_panel.table_widget.verticalHeader().hide()
            self.admin_actions_panel.table_widget.insertRow(0)
            self.admin_actions_panel.table_widget.setItem(0, 0, QtWidgets.QTableWidgetItem("Предъявите персональный идентификатор"))
            self.admin_actions_panel.table_widget.resizeColumnsToContents()
            # Переименовать кнопки, т.к. в панелях инициализации некоторые называются по-другому
            self.common_parms_panel.save_push_button.setText("Вперед")
            self.common_parms_panel.cancel_push_button.setText("Назад")
            self.passwd_parms_panel.save_push_button.setText("Вперед")
            self.passwd_parms_panel.cancel_push_button.setText("Назад")
            self.integrity_control_panel.save_push_button.setText("Вперед")
            self.integrity_control_panel.cancel_push_button.hide()

            self.sys_parms_panel.next_push_button.clicked.connect(functools.partial(self.show_init_panel, 1))
            self.common_parms_panel.cancel_push_button.clicked.connect(functools.partial(self.show_init_panel, 0))
            self.common_parms_panel.save_push_button.clicked.connect(functools.partial(self.show_init_panel, 2))
            self.journal_parms_panel.cancel_push_button.clicked.connect(functools.partial(self.show_init_panel, 1))
            self.journal_parms_panel.save_push_button.clicked.connect(functools.partial(self.show_init_panel, 3))
            self.journal_parms_panel.default_push_button.clicked.connect(functools.partial(self.set_default_settings, self.journal_parms_panel))
            self.passwd_parms_panel.cancel_push_button.clicked.connect(functools.partial(self.show_init_panel, 2))
            self.passwd_parms_panel.save_push_button.clicked.connect(functools.partial(self.show_init_panel, 4))
            self.admin_actions_panel.back_push_button.clicked.connect(functools.partial(self.show_init_panel, 3))
            self.admin_actions_panel.yes_push_button.clicked.connect(self.next_admin_action_panel)
            self.admin_actions_panel.cancel_push_button_2.clicked.connect(functools.partial(self.show_init_panel, 0))
            self.admin_actions_panel.next_push_button_2.clicked.connect(self.check_admin_passwd)
            self.admin_actions_panel.cancel_push_button_3.clicked.connect(functools.partial(self.show_init_panel, 0))
            self.admin_actions_panel.next_push_button_3.clicked.connect(functools.partial(self.show_init_panel, 5))
            self.admin_actions_panel.passwd_line_edit.textChanged[str].connect(self.admin_passwd_changed)
            self.admin_actions_panel.passwd_confirm_line_edit.textChanged[str].connect(self.admin_passwd_changed)
            self.admin_actions_panel.show_passwd_radio_button.clicked.connect(self.toggle_admin_passwd_visibility)
            self.admin_actions_panel.passwd_gen_push_button.clicked.connect(self.gen_admin_passwd)
            self.integrity_control_panel.save_push_button.clicked.connect(self.show_complete_dialog)
            
            self.sys_parms_panel.sys_volume_value.setText(bootable_partition)
            self.sys_parms_panel.serial_ctl_value.setText(bootable_uuid)

            self.show_init_panel(0)

        # Связать сигналы и слоты в панелях, используемых в обоих режимах
        self.common_parms_panel.default_push_button.clicked.connect(functools.partial(self.set_default_settings, self.common_parms_panel))
        self.common_parms_panel.save_push_button.clicked.connect(functools.partial(self.save_panel_settings, self.common_parms_panel))
        self.passwd_parms_panel.passwd_difficulty_check_box.clicked.connect(self.toggle_passwd_difficulty_check)
        self.passwd_parms_panel.default_push_button.clicked.connect(functools.partial(self.set_default_settings, self.passwd_parms_panel))
        self.passwd_parms_panel.save_push_button.clicked.connect(functools.partial(self.save_panel_settings, self.passwd_parms_panel))

        # Содержание предъявленной iButton
        self.presented_ibutton = ""
        # Установить функцию обратного вызова для обработки сигнала IButtonSignal
        bus.add_signal_receiver(self.ibutton_signal_handler, bus_name='com.example.IButtonService', signal_name="IButtonSignal")
        # Получить объект шины
        self.service_object = bus.get_object('com.example.IButtonService', '/com/example/IButtonService')

        self.show()

    def show_main_panel(self, index: int):
        """Показать выбранную панель настроек с сохраненными настройками"""
        self.settings_stacked_widget.setCurrentIndex(index)
        # Установить значения элементов выбранной панели в соответствии с настройками
        panel = self.settings_stacked_widget.widget(index)
        self.set_saved_settings(panel)

    def show_init_panel(self, index: int):
        """Показать выбранную панель инициализации с сохраненными настройками"""
        self.admin_actions_panel.stacked_widget.setCurrentIndex(0)
        self.init_panel.stacked_widget.setCurrentIndex(index)

        # Список меток, отображающих шаги инициализации (по 2 на шаг)
        labels = (
            self.init_panel.label_1,
            self.init_panel.label_2,
            self.init_panel.label_3,
            self.init_panel.label_4,
            self.init_panel.label_5,
            self.init_panel.label_6,
            self.init_panel.label_7,
            self.init_panel.label_8,
            self.init_panel.label_9,
            self.init_panel.label_10,
            self.init_panel.label_11,
            self.init_panel.label_12
        )
        # Выделить метку, соответствующую текущему шагу (index) инициализации
        for i in range(len(labels)):
            if i == 2 * index or i == 2 * index + 1:
                labels[i].setStyleSheet("""
                    background-color: #48A23F;
                    color: white;
                """)
            else:
                labels[i].setStyleSheet("""
                    background-color: white;
                    color: black;
                """)

        if not index:
            self.sys_parms_panel.sys_datetime_line_edit.setText(datetime.datetime.now().strftime("%H:%M %d/%m/%Y"))

    def show_journal_panel(self, index):
        """Показать выбранную панель журнала событий"""
        self.event_journal_panel.journal_stacked_widget.setCurrentIndex(index)
        self.set_saved_settings(self.event_journal_panel)

    def set_saved_settings(self, panel):
        """Установить сохраненные настройки panel"""
        panel_name = panel.objectName()
        logging.debug(f"Set {panel_name} settings")
        try:
            # Прочитать значения сохраненных настроек в секции panel_name и
            # в соответствии с ними установить значения элементов
            for widget_name, value in self.config.items(panel_name):
                if isinstance(getattr(panel, widget_name), QCheckBox):
                    getattr(panel, widget_name).setChecked(str2bool(value))
                elif isinstance(getattr(panel, widget_name), QLineEdit):
                    getattr(panel, widget_name).setText(value)
                elif isinstance(getattr(panel, widget_name), QComboBox):
                    getattr(panel, widget_name).setCurrentIndex(int(value))
        except (configparser.NoSectionError, AttributeError) as e:
            logging.debug(e)

    def set_default_settings(self, panel):
        """Установить дефолтные настройки panel из ui-файла"""
        # stack_widget в котором находится panel
        parent = panel.parentWidget()
        index = parent.indexOf(panel)
        if index == -1:
            logging.error(f"Index of {panel.objectName()} is't founded")
            return
        # Получить имя ui-файла
        panel_name = panel.objectName()
        try:
            ui_file = self.settings_panels[panel_name]
        except KeyError:
            ui_file = self.init_panels[panel_name]

        logging.debug(f"Set default settings for {panel_name}")
        # Загрузить дефтную панель из ui-файла
        default_panel = self.loader.loadUi(os.path.join(CURRENT_DIR, ui_file))
        default_panel.setObjectName(panel_name)
        setattr(self, panel_name, default_panel)
        # Удалить панель из стека (но не из памяти)
        parent.removeWidget(panel)
        # Удалить панель из памяти в цикле событий Qt
        panel.deleteLater()
        # Вставить панель с дефолтными настройками
        parent.insertWidget(index, default_panel)
        parent.setCurrentIndex(index)
        # Заново связать сигналы и слоты (по-разному в зависимости от режима)
        if self.admins:
            getattr(self, panel_name).default_push_button.clicked.connect(functools.partial(self.set_default_settings, getattr(self, panel_name)))
            getattr(self, panel_name).save_push_button.clicked.connect(functools.partial(self.save_panel_settings, getattr(self, panel_name)))
        else:
            getattr(self, panel_name).default_push_button.clicked.connect(functools.partial(self.set_default_settings, getattr(self, panel_name)))
            getattr(self, panel_name).save_push_button.setText("Вперед")
            getattr(self, panel_name).save_push_button.clicked.connect(functools.partial(self.show_init_panel, index + 1))
            getattr(self, panel_name).cancel_push_button.setText("Назад")
            getattr(self, panel_name).cancel_push_button.clicked.connect(functools.partial(self.show_init_panel, index - 1))

    def save_panel_settings(self, panel):
        """Сохранить настройки panel"""
        panel_name = panel.objectName()
        logging.debug(f"Save {panel_name} settings")
        for name, obj in inspect.getmembers(getattr(self, panel_name)):
            # Сохранить установки только для элементов перечисленных типов
            if any(isinstance(obj, t) for t in (QLineEdit, QCheckBox, QComboBox)):
                widget_name = obj.objectName()
                if isinstance(obj, QCheckBox):
                    value = obj.isChecked()
                elif isinstance(obj, QLineEdit):
                    value = obj.text()
                elif isinstance(obj, QComboBox):
                    value = obj.currentIndex()
                # Если отсутствует, то создать секцию с именем, соответствующим названию панели
                if not self.config.has_section(panel_name):
                    self.config.add_section(panel_name)
                # Сохранить значение value в параметре widget_name секции panel_name,
                self.config.set(panel_name, widget_name, str(value))

    def trigger_events_time_search(self):
        """Изменить состояние элементов управления фильтрации событий по времени"""
        self.event_journal_panel.events_start_time_line_edit.setEnabled(self.event_journal_panel.events_time_search_check_box.isChecked())
        self.event_journal_panel.events_end_time_line_edit.setEnabled(self.event_journal_panel.events_time_search_check_box.isChecked())

    def trigger_events_type_search(self):
        """Изменить состояние элементов управления фильтрации событий по типам"""
        self.event_journal_panel.events_type_list_widget.setEnabled(self.event_journal_panel.events_type_search_check_box.isChecked())
        self.event_journal_panel.select_all_push_button.setEnabled(self.event_journal_panel.events_type_search_check_box.isChecked())
        self.event_journal_panel.clear_all_push_button.setEnabled(self.event_journal_panel.events_type_search_check_box.isChecked())

    def decrease_remaining_time(self):
        """Уменьшить счетчик времени до входа в систему"""
        self.remaining_time -= 1
        if self.remaining_time == 0:
            # TODO Вместо сброса счетчика, блокировать вход для все пользователей, кроме администратора
            logging.info("The waiting time has expired")
            self.remaining_time = int(self.config.get("common_parms_panel", "time_limit_line_edit")) * 60
            self.ibutton_present[dict].connect(self.read_ibutton)
            self.main_stacked_widget.setCurrentIndex(WAIT_ID_PAGE)
        else:
            # TODO Перевести секунды в минуты и секунды
            self.remaining_time_label_1.setText(f"До окончания входа в систему осталось: {self.remaining_time} сек.")
            self.remaining_time_label_2.setText(f"До окончания входа в систему осталось: {self.remaining_time} сек.")

    def read_ibutton(self, message):
        """Сохранить предъявленный идентификатор пользователя и перейти на панель ввода пароля"""
        self.presented_ibutton = message
        # Отключить обработчик "прикладывания" iButton
        self.ibutton_present[dict].disconnect()
        self.id_label.setText(self.presented_ibutton["id"])
        # Стереть поле ввода пароля на случай попытки повторного входа
        self.passwd_line_edit.setText("")
        self.passwd_line_edit.setFocus()
        self.main_stacked_widget.setCurrentIndex(PASSWD_PAGE)

    def ibutton_signal_handler(self, message):
        """Функция обратного вызова для обработки сигнала с dBus"""
        logging.debug(f"Recieve message: {message}")
        self.ibutton_present.emit(message)

    def auth_user(self):
        """Проверить предъявленный идентификатор и пароль"""
        # Найти в списке self.users индекс пользователя iButton которого предъявлен или None, если не найден
        try:
            index = [i["id"] for i in self.users].index(self.presented_ibutton["id"])
        except ValueError:
            index = None

        if self.presented_ibutton["passwd"] == self.passwd_line_edit.text():
            # Веден правильный пароль, остановить таймер открыть панель выбора действия Загрузка ОС/Настройки
            self.timer.stop()
            # Если входящий пользователь в списке self.admins, открыть страницу настроек и выйти
            if self.presented_ibutton["id"] in self.admins:
                # Заполнить поля в окне выбора действий, доступных администратору
                self.failed_logins_value.setText(str(self.failed_logins))
                # Найти пользователя входившего в систему последним
                last_user = self.users[0]
                for user in self.users:
                    if user["last_login_datetime"] > last_user["last_login_datetime"]:
                        last_user = user
                self.last_user_name_value.setText(last_user["user_name"])
                self.last_user_id_value.setText(last_user["id"])
                self.last_user_datetime_value.setText(last_user["last_login_datetime"].strftime("%H:%M %Y/%m/%d"))
                self.admin_id_value.setText(self.presented_ibutton["id"])
                self.admin_datetime_value.setText(datetime.datetime.now().strftime("%H:%M %Y/%m/%d"))
                # Перейти на страницу выбора действий, доступных администратору
                self.main_stacked_widget.setCurrentIndex(ADMIN_CHOICE_PAGE)
            else:
                # TODO Проверить, что пользователь не заблокирован
                pass
                # TODO Показать статистику, только если установлен соответствующий параметр
                pass
                # Заполнить поля в окне выбора действий, доступных пользователю
                self.user_name_value.setText(self.users[index]["user_name"])
                self.user_id_value.setText(self.users[index]["id"])
                self.user_datetime_value.setText(datetime.datetime.now().strftime("%H:%M %Y/%m/%d"))
                self.user_last_datetime_value.setText(self.users[index]["last_login_datetime"].strftime("%H:%M %Y/%m/%d"))
                self.user_logins_count_value.setText(str(self.users[index]["total_logins"]))
                # Вычислить срок действия пароля и число дней до устаревания
                passwd_age = (datetime.datetime.now() - self.users[index]["passwd_datetime"]).days
                remaining_days = int(self.config.get("passwd_parms_panel", "passwd_age_line_edit")) - passwd_age
                self.user_remaining_days_value.setText(str(remaining_days))
                # Сбросить счетчик неудачных попыток входа, инкрементировать счетчик общего количества попыток входа
                self.users[index]["failed_logins"] = 0
                self.users[index]["total_logins"] += 1
                self.users[index]["last_login_datetime"] = datetime.datetime.now()
                # Перейти на страницу выбора действий, доступных пользователю
                self.main_stacked_widget.setCurrentIndex(USER_CHOICE_PAGE)
        else:
            # Введен неправильный пароль
            logging.info(f"Fail login, user index {index}")
            self.failed_logins += 1
            # Если это обычный пользователь, то увеличить число неудачных попыток входа
            if index is not None:
                self.users[index]["failed_logins"] += 1
                # TODO Заблокировать пользователя, если превышено максимальное число неверных попыток входа
                pass
            QtWidgets.QMessageBox.warning(self, "Quit", "Неверный идентификатор или пароль", QtWidgets.QMessageBox.Ok)
            self.ibutton_present[dict].connect(self.read_ibutton)
            self.main_stacked_widget.setCurrentIndex(WAIT_ID_PAGE)

    def toggle_passwd_difficulty_check(self):
        """Изменить состояние элементов управления параметрами сложности паролей
           при включенеии/отключении контроля сложности"""
        difficulty_check = self.passwd_parms_panel.passwd_difficulty_check_box.isChecked()
        # Пока в ToggleBox нет обозначения цветом всех трех состояний checked, unchecked, disabled,
        # остальные элементы лучше не отключать, иначе дезориентируем пользователя
        return
        self.passwd_parms_panel.digit_present_check_box.setEnabled(difficulty_check)
        self.passwd_parms_panel.upcase_letter_check_box.setEnabled(difficulty_check)
        self.passwd_parms_panel.lowercase_letter_check_box.setEnabled(difficulty_check)
        self.passwd_parms_panel.special_char_check_box.setEnabled(difficulty_check)
        self.passwd_parms_panel.repeating_char_check_box.setEnabled(difficulty_check)
        self.passwd_parms_panel.repeating_digit_check_box.setEnabled(difficulty_check)

    def show_user_creation_wizard(self):
        """Скрыть боковое меню и показать первую панель мастера создания нового пользователя"""
        self.settings_sidebar_widget.hide()
        self.user_actions_panel.stacked_widget.setCurrentWidget(self.user_actions_panel.page_1)
        # Установить исходные значения виджетов
        self.user_actions_panel.user_name.setText("")
        self.user_actions_panel.passwd_line_edit.setText("")
        self.user_actions_panel.passwd_confirm_line_edit.setText("")
        self.user_actions_panel.ibutton_label.setText("Предъявите персональный идентификатор")
        self.user_actions_panel.cancel_push_button_4.setEnabled(True)
        self.user_actions_panel.finish_push_button_4.setEnabled(False)

        self.stackedWidget.setCurrentWidget(self.user_actions_panel)

    def add_user(self, message: Dict[str, str]):
        """Добавить пользователя, id которого указана в словаре message"""
        # Метод вызывается по сигналу предъявления iButton,
        # в message передается словарь с id, user_name и passwd, считанные изпредъявленной ibutton
        logging.info(message)
        # Отключить обработчик "прикладывания" iButton
        self.ibutton_present[dict].disconnect()

        # Добавить новую запись в список пользователей
        self.users.append({
            "id": str(message["id"]),
            "user_name": self.user_actions_panel.user_name.text(),
            "passwd_datetime": datetime.datetime.now(),
            "last_login_datetime": datetime.datetime(1, 1, 1, 0, 0),
            "total_logins": 0,
            "failed_logins": 0,
            "ext_media_prohib": True,
            "ch_passwd_prohib": False,
            "passwd_age_limit": True,
            "user_id_change": True,
            "user_status": 0,
            "integrity_ctl_mode": 0
        })

        # Вызвать метод для записи в предъявленную ibutton имени и пароля пользователя
        self.service_object.SetIButtonData({
            "id": str(message["id"]),
            "user_name": self.user_actions_panel.user_name.text(),
            "passwd": self.user_actions_panel.passwd_line_edit.text()
        })

        self.user_actions_panel.ibutton_label.setText(f"Предъявлен идентификатор: {message['id']}\nПользователь успешно зарегистрирован.")
        self.user_actions_panel.finish_push_button_4.setEnabled(True)
        self.user_actions_panel.cancel_push_button_4.setEnabled(False)
        self.update_user_list_panel()

    def del_user(self):
        """Удалить выбранного пользователя"""
        index = self.user_list_panel.user_list_widget.currentRow()
        self.users.pop(index)
        self.update_user_list_panel()

    def del_all_users(self):
        """Удалить всех всех пользователей"""
        self.users.clear()
        self.update_user_list_panel()

    def close_user_ctl_wizard(self):
        """Отменить работу мастера создания нового пользователя,
        показать боковое меню и панель с списком пользователей"""
        self.settings_sidebar_widget.show()
        self.stackedWidget.setCurrentWidget(self.user_list_panel)

    def user_name_changed(self, text: str):
        """Изменить состояние кнопки "Вперед" при вводе имени нового пользователя"""
        self.user_actions_panel.next_push_button_1.setEnabled(bool(len(text)))

    def check_user_name(self):
        """Проверить уникальность имени нового пользователя"""
        logging.info(self.user_actions_panel.user_name.text())
        # TODO Уточнить могут ли быть пользователи с одинаковыми именами или нет, если могут исключить проверку,
        # иначе реализовать проверку и при совпадении self.user_actions_panel.user_name.text() с существуюшим пользователем
        # выдать предупреждающее сообщение
        self.user_actions_panel.stacked_widget.setCurrentWidget(self.user_actions_panel.page_2)

    def next_user_action_panel(self):
        """Перейти на следующую панель мастера управления пользователями"""
        self.user_actions_panel.stacked_widget.setCurrentIndex(self.user_actions_panel.stacked_widget.currentIndex() + 1)

    def user_passwd_changed(self, text):
        """Изменить состояние кнопки "Вперед" при наличии символов в обоих полях ввода пароля"""
        if len(self.user_actions_panel.passwd_line_edit.text()) != 0 and len(self.user_actions_panel.passwd_confirm_line_edit.text()) != 0:
            self.user_actions_panel.next_push_button_3.setEnabled(True)
        else:
            self.user_actions_panel.next_push_button_3.setEnabled(False)

    def toggle_user_passwd_visibility(self):
        """Переключить видимость пароля пользователя в полях ввода"""
        if self.user_actions_panel.show_passwd_radio_button.isChecked():
            self.user_actions_panel.passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.user_actions_panel.passwd_confirm_line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.user_actions_panel.passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
            self.user_actions_panel.passwd_confirm_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)

    def gen_user_passwd(self):
        """Сгенерировать пароль пользователя и показать его в полях ввода"""
        user_passwd = gen_password(int(self.passwd_parms_panel.min_passwd_len_line_edit.text()))
        self.user_actions_panel.passwd_line_edit.setText(user_passwd)
        self.user_actions_panel.passwd_confirm_line_edit.setText(user_passwd)
        self.user_actions_panel.show_passwd_radio_button.setChecked(True)
        self.toggle_user_passwd_visibility()

    def check_user_passwd(self):
        """Проверить совпадение пароля в обоих полях ввода и его соответствие требованиям сложности"""
        if self.user_actions_panel.passwd_line_edit.text() != self.user_actions_panel.passwd_confirm_line_edit.text():
            # QtWidgets.QMessageBox.warning(self, "Ошибка", "Введенные пароли не совпадают, повторите ввод!", QtWidgets.QMessageBox.Ok)
            sobol_dialog = SobolDialog("Введенные пароли не совпадают, повторите ввод!")
            sobol_dialog.exec()
            return
        # Перед открытием последней панели мастера добавления пользователей связать сигнал предъявления ibutton с обработчиком self.add_user
        self.ibutton_present[dict].connect(self.add_user)
        self.next_user_action_panel()

    def update_user_list_panel(self):
        """Обновить панель со списком пользователей"""
        self.user_list_panel.user_list_widget.clear()
        for user in self.users:
            # TODO Исключить из списка администратора безопасности
            self.user_list_panel.user_list_widget.addItem(user["user_name"])
        self.user_list_panel.user_list_widget.setCurrentRow(0)
        self.show_user_parms(self.user_list_panel.user_list_widget.currentItem())

    def show_user_parms(self, item):
        """Показать настройки выбранного в списке пользователя"""
        index = self.user_list_panel.user_list_widget.currentRow()
        logging.debug(f"Select user: {self.users[index]['user_name']}")
        user = self.users[index]
        try:
            self.user_list_panel.user_id.setText(user["id"])
            self.user_list_panel.user_name.setText(user["user_name"])
            self.user_list_panel.last_login_datetime.setText(user["last_login_datetime"].strftime("%H:%M %Y/%m/%d"))
            self.user_list_panel.total_logins.setText(str(user["total_logins"]))
            self.user_list_panel.failed_logins.setText(str(user["failed_logins"]))
            self.user_list_panel.ext_media_prohib.setChecked(bool(user["ext_media_prohib"]))
            self.user_list_panel.ch_passwd_prohib.setChecked(bool(user["ch_passwd_prohib"]))
            self.user_list_panel.passwd_age_limit.setChecked(bool(user["passwd_age_limit"]))
            self.user_list_panel.user_id_change.setChecked(bool(user["user_id_change"]))
            self.user_list_panel.user_status.setCurrentIndex(user["user_status"])
            self.user_list_panel.integrity_ctl_mode.setCurrentIndex(user["integrity_ctl_mode"])
        except KeyError as e:
            logging.debug(e)

    def save_user_parms(self):
        """Сохранить настройки выбранного в списке пользователя"""
        index = self.user_list_panel.user_list_widget.currentRow()
        logging.info(f"Selected user is {self.users[index]}")
        self.users[index]["ext_media_prohib"] = self.user_list_panel.ext_media_prohib.isChecked()
        self.users[index]["ch_passwd_prohib"] = self.user_list_panel.ch_passwd_prohib.isChecked()
        self.users[index]["passwd_age_limit"] = self.user_list_panel.passwd_age_limit.isChecked()
        self.users[index]["user_id_change"] = self.user_list_panel.user_id_change.isChecked()
        self.users[index]["user_status"] = self.user_list_panel.user_status.currentIndex()
        self.users[index]["integrity_ctl_mode"] = self.user_list_panel.integrity_ctl_mode.currentIndex()

    def next_admin_action_panel(self):
        """Перейти на следующую панель мастера регистрации администратора"""
        self.admin_actions_panel.stacked_widget.setCurrentIndex(self.admin_actions_panel.stacked_widget.currentIndex() + 1)

    def admin_passwd_changed(self, text: str):
        """Изменить состояние кнопки "Вперед" при наличии символов в обоих полях ввода пароля"""
        if len(self.admin_actions_panel.passwd_line_edit.text()) != 0 and len(self.admin_actions_panel.passwd_confirm_line_edit.text()) != 0:
            self.admin_actions_panel.next_push_button_2.setEnabled(True)
        else:
            self.admin_actions_panel.next_push_button_2.setEnabled(False)

    def gen_admin_passwd(self):
        """Сгенерировать пароль администратора и показать его в полях ввода"""
        admin_passwd = gen_password(int(self.passwd_parms_panel.min_passwd_len_line_edit.text()))
        self.admin_actions_panel.passwd_line_edit.setText(admin_passwd)
        self.admin_actions_panel.passwd_confirm_line_edit.setText(admin_passwd)
        self.admin_actions_panel.show_passwd_radio_button.setChecked(True)
        self.toggle_admin_passwd_visibility()

    def toggle_admin_passwd_visibility(self):
        """Переключить видимость пароля администратора в полях ввода"""
        if self.admin_actions_panel.show_passwd_radio_button.isChecked():
            self.admin_actions_panel.passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.admin_actions_panel.passwd_confirm_line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.admin_actions_panel.passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
            self.admin_actions_panel.passwd_confirm_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)

    def check_admin_passwd(self):
        """Проверить совпадение пароля в обоих полях ввода и его соответствие требованиям сложности"""
        if self.admin_actions_panel.passwd_line_edit.text() != self.admin_actions_panel.passwd_confirm_line_edit.text():
            # QtWidgets.QMessageBox.warning(self, "Ошибка", "Введенные пароли не совпадают, повторите ввод!", QtWidgets.QMessageBox.Ok)
            sobol_dialog = SobolDialog("Введенные пароли не совпадают, повторите ввод!")
            sobol_dialog.exec()
            return
        # Перед открытием последней панели мастера дрегистрации администратора связать сигнал предъявления ibutton с обработчиком self.add_admin
        self.ibutton_present[dict].connect(self.add_admin)
        self.next_admin_action_panel()

    def add_admin(self, message: Dict[str, str]):
        """Зарегистрировать администратора id которого указана в словаре message"""
        # Метод вызывается по сигналу предъявления iButton,
        # в message передается словарь с id, user_name и passwd, считанные изпредъявленной ibutton
        logging.info(message)
        # Отключить обработчик "прикладывания" iButton
        self.ibutton_present[dict].disconnect()

        self.admins.append(str(message["id"]))
        # TODO Записать пароль администратора, для этого вызвать метод SetIButtonData, зарегистрированный в dbus
        message["user_name"] = "Администратор"
        message["passwd"] = self.admin_actions_panel.passwd_line_edit.text()
        logging.info(str(message))

        # Вызвать метод для записи в предъявленную ibutton имени и пароля администратора
        self.service_object.SetIButtonData({
            "id": str(message["id"]),
            "user_name": "Администратор",
            "passwd": self.admin_actions_panel.passwd_line_edit.text()
        })

        row = self.admin_actions_panel.table_widget.rowCount() - 1
        self.admin_actions_panel.table_widget.setItem(row, 1, QtWidgets.QTableWidgetItem(str(message["id"])))
        self.admin_actions_panel.table_widget.setItem(row, 2, QtWidgets.QTableWidgetItem("Администратор зарегистирован"))
        self.admin_actions_panel.table_widget.resizeColumnsToContents()
        self.admin_actions_panel.next_push_button_3.setEnabled(True)

    def show_complete_dialog(self):
        sobol_dialog = SobolDialog("Включен контроль целостности, но не\nрассчитаны контрольные суммы.\nВы уверены, что хотите продолжить?")
        result = sobol_dialog.exec()
        if result == QtWidgets.QDialog.Accepted:
            self.close()

    def sys_load(self):
        """Запустить виртуальную машину и открыть virt-viewer"""
        try:
            self.dom.create()
            logging.info("Domain %s created" % self.domain_name)
        except libvirt.libvirtError as e:
            logging.error(e)
        """
        # Вариант с отображением рабочего стола виртуальной машины во встроенном QWebEngineView
        self.main_stacked_widget.setCurrentIndex(WEB_VIEW_PAGE)
        # Если url вводится пользователем, лучше использовать метод QtCore.QUrl.fromUserInput(url),
        # чтобы при необходимости добавить название протокола и т.п.
        url = QtCore.QUrl(self.config.get("general", "vnc_url"))
        logging.debug(f"Open {url}")
        self.web_engine_view.load(url)
        return
        """
        subprocess.Popen(["virt-viewer", self.domain_name])
        self.close()

    def closeEvent(self, event):
        """Сохранить настройки приложения"""
        # Получить кортеж с элементами QRect геометрии главного окна
        geometry = self.geometry().getRect()
        # Преобразовать элементы кортежа в строки и разделить символом ;
        self.config.set("window", "geometry", ";".join(map(str, geometry)))
        self.config.set("window", "state", str(int(self.windowState())))
        # Сохранить учетные записи пользователей и суммарное кол-во неудачных попыток входа
        self.config.set("general", "users", str(self.users))
        self.config.set("general", "admins", str(self.admins))
        self.config.set("general", "failed_logins", str(self.failed_logins))
        with open(self.config_file, "w") as file:
            self.config.write(file)
