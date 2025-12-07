import configparser
import datetime
import functools
import inspect
import logging
import os
import sys

from distutils.util import strtobool

from PySide2 import QtCore, QtGui, QtUiTools, QtWidgets
from PySide2.QtWidgets import QLineEdit, QCheckBox, QComboBox

import dbus
import dbus.mainloop.glib

from BackgroundedWidget import BackgroundedWidget
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
SETTINGS_PAGE = 3
WEB_VIEW_PAGE = 4
VM_IFACE_PAGE = 5


class MainWindow(QtWidgets.QMainWindow):
    # Сигнал "предъявления" iButton
    ibutton_present = QtCore.Signal(dict)

    def __init__(self, config_file):
        super().__init__()

        loader = QtUiTools.QUiLoader()
        loader.registerCustomWidget(BackgroundedWidget)

        self.window = loader.load(os.path.join(CURRENT_DIR, "MainWindow.ui"), None)

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
            # Имя виртуальной машины
            self.domain_name = self.config.get("general", "domain_name")
            # Адрес инструкции к выполнению задания
            self.instruction_url = self.config.get("general", "instruction_url")
            # Адрес и порт VNC-сервера виртуальной машины
            self.vnc_addr = self.config.get("general", "vnc_addr")
            self.vnc_port = int(self.config.get("general", "vnc_port"))

            self.window.setWindowTitle(self.config.get("window", "title"))
            # Разбить строку на элементы, преобразовать их в целые числа и получить QRect с геометрией главного окна
            geometry = QtCore.QRect(*map(int, self.config.get("window", "geometry").split(";")))
            # Восстановить геометрию главного окна
            self.window.setGeometry(geometry)

            state = int(self.config.get("window", "state"))
            self.window.restoreState(bytearray(state))
        except configparser.NoOptionError as e:
            logging.warning(e)
        except configparser.NoSectionError as e:
            logging.error(e)

        # Создать боковую панель (sidebar)
        self.sidebar_widget = QtWidgets.QWidget()
        # Установить фиксированную ширину боковой панели
        self.sidebar_widget.setFixedWidth(230)
        self.sidebar_widget.setContentsMargins(0, 0, 0, 0)

        # Настроить параметры отображения боковой панели
        self.sidebar_widget.setStyleSheet("""
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
        """)

        # Создать менеджер компоновки с кнопками меню
        sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        buttons = {
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
        verticalSpacer = QtWidgets.QSpacerItem(20, 15, QtWidgets.QSizePolicy.Fixed)
        sidebar_layout.addItem(verticalSpacer)
        for i, item in enumerate(buttons.items()):
            button = QtWidgets.QPushButton(item[0])
            button.setIcon(QtGui.QIcon(item[1]))
            sidebar_layout.addWidget(button)
            # Связать событие нажания кнопки с обработчиком, передавая в обработчик номер кнопки
            button.clicked.connect(functools.partial(self.show_main_panel, i))
        verticalSpacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sidebar_layout.addItem(verticalSpacer)
        # Вставить созданный менеджер компоновки в нулевую позицию менеджера компоновки главного окна (mainHorizontalLayout)
        self.window.mainHorizontalLayout.insertWidget(0, self.sidebar_widget, alignment=QtCore.Qt.AlignLeft)

        # Динамически добавить панели в стек виджетов, с последующим обращением к ним self.sys_load_panel и т.д.
        self.panels = {
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
        loader = QtUiTools.QUiLoader()
        loader.registerCustomWidget(Toggle)

        for panel_name, ui_file in self.panels.items():
            # Динамически загрузить панели и добавить в stackedWidget
            panel = loader.load(os.path.join(CURRENT_DIR, ui_file))
            # Установить имя панели, для использования при установке сохраненных настроек
            panel.setObjectName(panel_name)
            setattr(self, panel_name, panel)
            self.window.stackedWidget.addWidget(getattr(self, panel_name))

        # При запуске открыть панель WAIT_ID_PAGE
        self.show_main_panel(WAIT_ID_PAGE)

        self.show_journal_panel(0)

        self.sys_load_panel.save_push_button.clicked.connect(functools.partial(self.save_panel_settings, self.sys_load_panel))
        self.common_parms_panel.save_push_button.clicked.connect(functools.partial(self.save_panel_settings, self.common_parms_panel))
        self.passwd_parms_panel.save_push_button.clicked.connect(functools.partial(self.save_panel_settings, self.passwd_parms_panel))
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
        self.user_actions_panel.passwd_line_edit_1.textChanged[str].connect(self.user_passwd_changed)
        self.user_actions_panel.passwd_line_edit_2.textChanged[str].connect(self.user_passwd_changed)
        self.user_actions_panel.next_push_button_3.clicked.connect(self.check_user_passwd)

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
        self.window.passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)

        # Связать сигнал и слоты
        self.window.enter_push_button.clicked.connect(self.auth_user)
        self.window.passwd_line_edit.returnPressed.connect(self.auth_user)
        # Чтобы не писать отдельный обработчик вызываем метод setCurrentIndex с передачей ему номера панели
        self.window.go_settings_push_button.clicked.connect(functools.partial(self.window.main_stacked_widget.setCurrentIndex, SETTINGS_PAGE))
        # Вызов метода закрытия с передачей ему кода возврата для последующего анализа и запуска виртуальной машины
        self.window.sys_load_push_button.clicked.connect(functools.partial(self.closeEvent, QtCore.QEvent.Enter))
        self.sys_load_panel.sys_load_push_button.clicked.connect(functools.partial(self.closeEvent, QtCore.QEvent.Enter))

        self.user_list_panel.add_user_push_button.clicked.connect(self.show_user_creation_wizard)
        self.user_list_panel.del_user_push_button.clicked.connect(self.del_user)
        self.user_list_panel.user_list_widget.itemClicked.connect(self.show_user_parms)
        self.user_list_panel.user_list_widget.itemActivated.connect(self.show_user_parms)
        self.user_list_panel.save_push_button.clicked.connect(self.save_user_parms)

        # Содержание предъявленной iButton
        self.presented_ibutton = ""

        self.timer = QtCore.QTimer()
        # Время до входа в систему, отображаемое в первых двух окнах
        self.remaining_time = int(self.config.get("common_parms_panel", "time_limit_line_edit")) * 60
        # Если 0, то не обрабатывать таймаут
        if self.remaining_time:
            self.timer.timeout.connect(self.decrease_remaining_time)

        # Установить функцию обратного вызова для обработки сигнала MySignal
        bus.add_signal_receiver(self.ibutton_signal_handler, bus_name='com.example.MyService', signal_name = "MySignal")
        
        # Пытаемся вызвать метод шины
        self.service_object = bus.get_object('com.example.MyService', '/com/example/MyService')

        # Запустить таймер ожидания чтения идентификатора iButton
        self.window.main_stacked_widget.setCurrentIndex(WAIT_ID_PAGE)
        self.ibutton_present[dict].connect(self.read_ibutton)
        self.timer.start(1000)

        # В отличии от PyQt в PySide виджет, загруженный с помощью QtUiTools,
        # не является окном, поэтому метод closeEvent для него не определен
        # Для выполнения действий при закрытии окна с загруженным виджетом необходимо
        # фильтровать события и при возникновении события Close вызвать необходимый метод
        self.window.installEventFilter(self)
        self.window.show()

    def eventFilter(self, watched, event):
        """Обработчик событий"""
        # Фильтр, перехватывающий возникновении события Close у виджетов, к которым он применен
        if watched is self.window and event.type() == QtCore.QEvent.Close:
            logging.info(f"Recieve event: {event}")
            self.closeEvent(event)
        return super().eventFilter(watched, event)

    def show_main_panel(self, index):
        """Показать выбранную панель настроек с сохраненными настройками"""
        self.window.stackedWidget.setCurrentIndex(index)
        # Установить значения элементов выбранной панели в соответствии с настройками
        panel = self.window.stackedWidget.widget(index)
        self.set_panel_settings(panel)

    def show_journal_panel(self, index):
        """Показать выбранную панель журнала событий"""
        self.event_journal_panel.journal_stacked_widget.setCurrentIndex(index)
        self.set_panel_settings(self.event_journal_panel)

    def set_panel_settings(self, panel):
        """Установить настройки панели panel"""
        panel_name = panel.objectName()
        logging.debug(f"Set {panel_name} settings")
        try:
            # Прочитать значения сохраненных настроек в секции panel_name и
            # в соответствии с ними установить значения элементов
            for widget_name, value in self.config.items(panel_name):
                if isinstance(getattr(panel, widget_name), QCheckBox):
                    getattr(panel, widget_name).setChecked(strtobool(value))
                elif isinstance(getattr(panel, widget_name), QLineEdit):
                    getattr(panel, widget_name).setText(value)
                elif isinstance(getattr(panel, widget_name), QComboBox):
                    getattr(panel, widget_name).setCurrentIndex(int(value))
        except (configparser.NoSectionError, AttributeError) as e:
            logging.debug(e)

    def save_panel_settings(self, panel):
        """Сохранить настройки панели panel"""
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
            self.window.main_stacked_widget.setCurrentIndex(WAIT_ID_PAGE)
        else:
            # TODO Перевести секунды в минуты и секунды
            self.window.remaining_time_label_1.setText(f"До окончания входа в систему осталось: {self.remaining_time} сек.")
            self.window.remaining_time_label_2.setText(f"До окончания входа в систему осталось: {self.remaining_time} сек.")

    def read_ibutton(self, message):
        """Сохранить предъявленный идентификатор пользователя и перейти на панель ввода пароля"""
        logging.info(f"Read {message} from iButton")
        self.presented_ibutton = message
        # Отключить обработчик "прикладывания" iButton
        self.ibutton_present[dict].disconnect()
        self.window.id_label.setText(self.presented_ibutton["id"])
        # Стереть поле ввода пароля на случай, если выполняем попытку повторного ввода
        self.window.passwd_line_edit.setText("")
        self.window.passwd_line_edit.setFocus()
        self.window.main_stacked_widget.setCurrentIndex(PASSWD_PAGE)

    def ibutton_signal_handler(self, message):
        """Функция обратного вызова для обработки сигнала с dBus"""
        logging.info(f"Recieve message: {message}")
        self.ibutton_present.emit(message)

    def auth_user(self):
        """Проверить предъявленный идентификатор и пароль"""
        for index, item in enumerate(self.users):
            if item["id"] == self.presented_ibutton["id"]:
                if self.presented_ibutton["passwd"] == self.window.passwd_line_edit.text():
                    # Веден правильный пароль, остановить таймер открыть панель выбора действия Загрузка ОС/Настройки
                    self.timer.stop()
                    self.users[index]["total_logins"] += 1
                    self.users[index]["last_login_datetime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.window.main_stacked_widget.setCurrentIndex(ADMIN_CHOICE_PAGE)
                    return
                # Введен неправильный пароль
                self.users[index]["failed_logins"] += 1

        # Если введен неправильный пароль, перейти в начало
        QtWidgets.QMessageBox.warning(self, "Quit", "Неверный идентификатор или пароль", QtWidgets.QMessageBox.Ok)
        self.ibutton_present[dict].connect(self.read_ibutton)
        self.window.main_stacked_widget.setCurrentIndex(WAIT_ID_PAGE)
        
    def show_user_creation_wizard(self):
        """Скрыть боковое меню и показать первую панель мастера создания нового пользователя"""
        self.sidebar_widget.hide()
        self.user_actions_panel.stacked_widget.setCurrentWidget(self.user_actions_panel.page_1)
        # Установить исходные значения виджетов
        self.user_actions_panel.user_name.setText("")
        self.user_actions_panel.passwd_line_edit_1.setText("")
        self.user_actions_panel.passwd_line_edit_2.setText("")
        self.user_actions_panel.ibutton_label.setText("Предъявите персональный идентификатор")
        self.user_actions_panel.cancel_push_button_4.setEnabled(True)
        self.user_actions_panel.finish_push_button_4.setEnabled(False)
        
        self.window.stackedWidget.setCurrentWidget(self.user_actions_panel)

    def add_user(self, message):
        """Добавить пользователя"""
        # Вызывается по сигналу предъявдения iButton
        logging.info(message)
        # Отключить обработчик "прикладывания" iButton
        self.ibutton_present[dict].disconnect()
        # Добавить новую запись в список пользователей
        self.users.append({
            "id": str(message["id"]),
            "user_name": self.user_actions_panel.user_name.text(),
            "last_login_datetime": "",
            "total_logins": 0,
            "failed_logins": 0,
            "ext_media_prohib": True,
            "ch_passwd_prohib": False,
            "passwd_age_limit": True,
            "user_id_change": True,
            "user_status": 0,
            "integrity_ctl_mode": 0
        })
        # TODO Вызвать метод для записи в предъявленную ibutton имени и пароля пользователя
        self.service_object.SetIButtonData({"id": str(message["id"]), "user_name": self.user_actions_panel.user_name.text(), "passwd": self.user_actions_panel.passwd_line_edit_1.text()})

        self.user_actions_panel.ibutton_label.setText(f"Предъявлен идентификатор: {message['id']}\nПользователь успешно зарегистрирован.")
        self.user_actions_panel.finish_push_button_4.setEnabled(True)
        self.user_actions_panel.cancel_push_button_4.setEnabled(False)
        self.update_user_list_panel()

    def del_user(self):
        """Удалить выбранного пользователя"""
        index = self.user_list_panel.user_list_widget.currentRow()
        self.users.pop(index)
        self.update_user_list_panel()

    def close_user_ctl_wizard(self):
        """Отменить работу мастера создания нового пользователя,
        показать боковое меню и панель с списком пользователей"""
        self.sidebar_widget.show()
        self.window.stackedWidget.setCurrentWidget(self.user_list_panel)

    def user_name_changed(self, text):
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
        if len(self.user_actions_panel.passwd_line_edit_1.text()) != 0 and len(self.user_actions_panel.passwd_line_edit_2.text()) != 0:
            self.user_actions_panel.next_push_button_3.setEnabled(True)
        else:
            self.user_actions_panel.next_push_button_3.setEnabled(False)

    def check_user_passwd(self):
        """Проверить совпадение пароля в обоих полях ввода и его соответствие требованиям сложности"""
        if self.user_actions_panel.passwd_line_edit_1.text() != self.user_actions_panel.passwd_line_edit_2.text():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введенные пароли не совпадают, повторите ввод!", QtWidgets.QMessageBox.Ok)
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
        logging.info(f"Selected user is {self.users[index]}")
        user = self.users[index]
        try:
            self.user_list_panel.user_id.setText(user["id"])
            self.user_list_panel.user_name.setText(user["user_name"])
            self.user_list_panel.last_login_datetime.setText(user["last_login_datetime"])
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

    def closeEvent(self, event):
        logging.debug(f"closeEvent {event}")

        # Получить кортеж с элементами QRect геометрии главного окна
        geometry = self.window.geometry().getRect()
        # Преобразовать элементы кортежа в строки и разделить символом ;
        self.config.set("window", "geometry", ";".join(map(str, geometry)))
        self.config.set("window", "state", str(int(self.window.windowState())))
        # Сохранить учетные записи пользователей
        self.config.set("general", "users", str(self.users))

        with open(self.config_file, "w") as file:
            self.config.write(file)

        if event is QtCore.QEvent.Type.Enter:
            exit_code = True
        else:
            exit_code = False

        # Вместо self.window.close() используем exit, чтобы вернуть код возврата,
        # для того, чтобы по нему понять нужно запускать виртуальную машину или нет
        QtCore.QCoreApplication.exit(exit_code)
