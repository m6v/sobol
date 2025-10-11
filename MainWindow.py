import configparser
import functools
import json
import logging
import os
import sys

import libvirt

from PySide2 import QtCore, QtWidgets
from PySide2.QtCore import Qt, QUrl, Signal, QRect, QTimer
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget, QSpacerItem, QSizePolicy, QLineEdit
from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PySide2.QtUiTools import QUiLoader

from pydbus import SessionBus
from gi.repository import GLib

from qvncwidget import QVNCWidget

from BackgroundedWidget import BackgroundedWidget
from toggle import Toggle

loop = GLib.MainLoop()
dbus_filter = "/com/example/MyService"
bus = SessionBus()

INITIAL_DIR = CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
# Если установлена переменная окружения _MEIPASS, программа запущена
# из временного каталога, созданного при распаковке бандла
if hasattr(sys, "_MEIPASS"):
    # Путь к временному каталогу взять из sys.executable
    INITIAL_DIR = os.path.dirname(sys.executable)

# Для логирования в файл, добавить filename='app.log' иначе лог в консоль
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

# Время, отводимое на вход в систему
REMAINING_TIME = 120

# Индексы панелей
WAIT_ID_PAGE = 0
PASSWD_PAGE = 1
ADMIN_CHOICE_PAGE = 2
SETTINGS_PAGE = 3
WEB_VIEW_PAGE = 4
VM_IFACE_PAGE = 5


class WebEnginePage(QWebEnginePage):
    navigation_request = Signal(str)

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        # Если переходить по ссылке не требуется, возвращаем False, иначе True
        if _type == QWebEnginePage.NavigationTypeLinkClicked:
            logging.debug(url.path())
            self.navigation_request.emit(url.path())
            # Здесь можно будет анализировать url и в зависимости от него
            # разрешать или запрещать переход по ссылке
            return False
        return True


class CustomWebEngineView(QWebEngineView):
    def __init__(self, *args, **kwargs):
        QWebEngineView.__init__(self, *args, **kwargs)
        self.setPage(WebEnginePage(self))


class MainWindow(QMainWindow):
    # Сигнал "предъявления" iButton
    ibutton_present = Signal(str)

    def __init__(self, config_file):
        super().__init__()

        loader = QUiLoader()
        loader.registerCustomWidget(BackgroundedWidget)

        self.window = loader.load(os.path.join(CURRENT_DIR, 'MainWindow.ui'), None)

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
            # Словарь, ключи которого - идентификатор iButton, значения - сведения об учетной записи (пароль, имя и др.)
            self.accounts = eval(self.config.get("general", "accounts"))
            # Имя виртуальной машины
            self.vm_name = self.config.get("general", "vm_name")
            # Название виртуальной машины в заголовок окна
            self.window.setWindowTitle(self.config.get("general", "vm_caption"))
            # Панель, отображаемая при запуске (instruction - инструкция, tbm - средство доверенной загрузки, vm - виртуальная машина)
            self.show_on_startup = self.config.get("general", "show_on_startup")
            # Адрес инструкции к выполнению задания
            self.instruction_url = self.config.get("general", "instruction_url")
            # Адрес и порт VNC-сервера виртуальной машины
            self.vnc_addr = self.config.get("general", "vnc_addr")
            self.vnc_port = int(self.config.get("general", "vnc_port"))

            # Разбить строку на элементы, преобразовать их в целые числа и получить QRect с геометрией главного окна
            geometry = QRect(*map(int, self.config.get('window', 'geometry').split(';')))
            # Восстановить геометрию главного окна
            self.window.setGeometry(geometry)

            state = int(self.config.get('window', 'state'))
            self.window.restoreState(bytearray(state))
        except configparser.NoOptionError as e:
            logging.warning(e)
        except configparser.NoSectionError as e:
            logging.error(e)
            print("!")

        # Create the sidebar widget
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setFixedWidth(230)  # Set a fixed width for the sidebar
        self.sidebar_widget.setContentsMargins(0, 0, 0, 0)

        # Apply background image using QSS
        self.sidebar_widget.setStyleSheet("""
            QWidget {
                font: 9pt 'Monospace Regular';
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

        # Создать боковую панель с кнопками меню
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        buttons = {"Загрузка ОС": "icons/sys_load.png",
                   "Режим работы": "icons/work_mode.png",
                   "Список пользователей": "icons/users_list.png",
                   "Журнал событий": "icons/journal.png",
                   "Общие параметры": "icons/common_parms.png",
                   "Параметры паролей": "icons/passwd_parms.png",
                   "Контроль целостности": "icons/integrity_control.png",
                   "Смена пароля": "icons/passwd_change.png",
                   "Смена аутентификатора": "icons/auth_id_change.png",
                   "Диагностика платы": "icons/diagnostic.png",
                   "Служебные операции": "icons/service_operations.png"
                   }
        verticalSpacer = QSpacerItem(20, 15, QSizePolicy.Fixed)
        sidebar_layout.addItem(verticalSpacer)
        for i, item in enumerate(buttons.items()):
            button = QPushButton(item[0])
            button.setIcon(QIcon(item[1]))
            sidebar_layout.addWidget(button)
            # Связать событие нажания кнопки с обработчиком, передавая в обработчик номер кнопки
            button.clicked.connect(functools.partial(self.menu_action_triggered, i))
        verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Preferred, QSizePolicy.Expanding)
        sidebar_layout.addItem(verticalSpacer)
        # Вставить созданный менеджер компоновки в нулевую позицию mainHorizontalLayout
        self.window.mainHorizontalLayout.insertWidget(0, self.sidebar_widget, alignment=Qt.AlignLeft)

        # Динамически добавить панели в стек виджетов,
        # с последующим обращением к ним self.sys_load_panel и т.д.
        panels = {'sys_load_panel': 'panels/SysLoadPanel.ui',
                  'work_mode_panel': 'panels/WorkModePanel.ui',
                  'user_list_panel': 'panels/UserListPanel.ui',
                  'event_journal_panel': 'panels/JournalPanel.ui',
                  'common_parms_panel': 'panels/CommonParmsPanel.ui',
                  'passwd_parms_panel': 'panels/PasswdParmsPanel.ui',
                  'integrity_control_panel': 'panels/IntegrityControlPanel.ui',
                  'passwd_change_panel': 'panels/PasswdChangePanel.ui',
                  'id_change_panel': 'panels/IdChangePanel.ui',
                  'diagnostic_panel': 'panels/DiagnosticPanel.ui',
                  'service_operations_panel': 'panels/ServiceOperationsPanel.ui'
                  }
        loader = QUiLoader()
        loader.registerCustomWidget(Toggle)

        for panel, form in panels.items():
            self.__dict__.update({panel: loader.load(os.path.join(CURRENT_DIR, form))})
            self.window.stackedWidget.addWidget(self.__dict__[panel])

        # state - состояние виртуальной машины, которое возвращается как число из перечисления virDomainState
        # reason - причина перехода в определённое состояние, которая возвращается как число из перечисления virDomain*Reason
        self.vm_state = False
        self.vm_reason = False
        try:
            # Register the default event implementation
            libvirt.virEventRegisterDefaultImpl()
            # Открыть соединение с локальным гипервизором
            self.conn = libvirt.open(None)
            if self.conn is None:
                logging.warning("Не удалось подключиться к libvirt")
            else:
                logging.info("Подключение к libvirt успешно")

            self.dom = self.conn.lookupByName(self.vm_name)
            self.vm_state, self.vm_reason = self.dom.state()
            logging.info("Domain %s state: %s, reason: %s" % (self.dom.name(), self.vm_state, self.vm_reason))

            # Зарегистрировать функцию обратного вызова для обработки событий от libvirt для всех доменов
            self.conn.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE, self.domain_event_callback, None)
            # Проверить нужна команда или нет?!
            libvirt.virEventRunDefaultImpl()
        except libvirt.libvirtError as e:
            logging.error(e)

        # Установка свойства в ui почему-то не работает, делаем здесь
        self.window.passwd_line_edit.setEchoMode(QLineEdit.Password)

        # Связать сигнал и слоты
        self.window.enter_push_button.clicked.connect(self.check_passwd)
        self.window.passwd_line_edit.returnPressed.connect(self.check_passwd)
        # Чтобы не писать отдельный обработчик вызываем метод setCurrentIndex с передачей ему номера панели
        self.window.go_settings_push_button.clicked.connect(functools.partial(self.window.main_stacked_widget.setCurrentIndex, SETTINGS_PAGE))
        self.window.load_sys_push_button.clicked.connect(self.load_sys)

        # Идентификатор считанной iButton
        self.auth_id = ""

        # Время до входа в систему, отображаемое в первых двух окнах
        self.remaining_time = REMAINING_TIME
        self.timer = QTimer()
        self.timer.timeout.connect(self.decrease_remaining_time)

        # Подписаться на получение сигналов с шины bus и
        # установить функцию обратного вызова для обработки сигнала
        bus.subscribe(object=dbus_filter, signal_fired=self.cb_server_signal_emission)

        # Добавить панель с веб-клиентом
        self.webEngineView = CustomWebEngineView()
        self.window.main_stacked_widget.addWidget(self.webEngineView)
        self.webEngineView.page().navigation_request[str].connect(self.init_training)

        # Добавить панель с VNC-клиентом
        self.vnc = QVNCWidget(
            parent=self,
            host=self.vnc_addr, port=self.vnc_port,
            password="",
            readOnly=False
        )
        self.window.main_stacked_widget.addWidget(self.vnc)

        # В зависимости от значения параметра show_on_startup отображаем указания к занятию,
        # интерфейс ПАК "Соболь" или интерфейс виртуальной машины
        if self.show_on_startup == "instruction":
            url = QUrl.fromUserInput(self.instruction_url)
            self.webEngineView.load(url)
            self.window.main_stacked_widget.setCurrentIndex(WEB_VIEW_PAGE)
        elif self.show_on_startup == "tbm":
            self.init_training("")
        else:
            self.load_sys()

        # В отличии от PyQt в PySide виджет, загруженный с помощью QtUiTools,
        # не является окном, поэтому метод closeEvent для него не определен
        # Для выполнения действий при закрытии окна с загруженным виджетом
        # фильтруем события и при возникновении события Close вызываем необходимый метод
        self.window.installEventFilter(self)
        self.window.show()

    def eventFilter(self, watched, event):
        if watched is self.window and event.type() == QtCore.QEvent.Close:
            self.closeEvent(event)
        return super().eventFilter(watched, event)

    def init_training(self, url):
        '''Инициировать начало тренировки открытием панели с интерфейсом ПАК "Соболь"
           или интерфейсом виртуальной машины, если она уже запущена'''
        logging.debug(url)

        if self.vm_state == libvirt.VIR_DOMAIN_RUNNING:
            # ВМ уже запущена, поэтому открыть панель с ее интерфейсом
            self.load_sys()
        else:
            # ВМ не запущена, поэтому ждать события о чтении идентификатора iButton
            self.window.main_stacked_widget.setCurrentIndex(WAIT_ID_PAGE)
            self.ibutton_present[str].connect(self.read_auth_id)
            self.timer.start(1000)

    def menu_action_triggered(self, index):
        '''Обработать событие выбора элемента меню настроек'''
        self.window.stackedWidget.setCurrentIndex(index)

    def decrease_remaining_time(self):
        '''Уменьшить счетчик времени до входа в систему'''
        self.remaining_time -= 1
        if self.remaining_time == 0:
            self.remaining_time = REMAINING_TIME
            self.ibutton_present[str].connect(self.read_auth_id)
            self.window.main_stacked_widget.setCurrentIndex(WAIT_ID_PAGE)
        else:
            # TODO Перевести секунды в минуты и секунды
            self.window.remaining_time_label_1.setText("До окончания входа в систему осталось: %s сек." % self.remaining_time)
            self.window.remaining_time_label_2.setText("До окончания входа в систему осталось: %s сек." % self.remaining_time)

    def read_auth_id(self, auth_id):
        '''Сохранить предъявленный идентификатор пользователя и перейти на панель ввода пароля'''
        logging.info("iButton %s is presented" % auth_id)
        self.auth_id = auth_id
        # Отключаем обработчик "прикладывания" iButton
        self.ibutton_present[str].disconnect()
        self.window.id_label.setText("iButton %s" % self.auth_id)
        # Стереть поле ввода пароля на случай, если выполняем попытку повторного ввода
        self.window.passwd_line_edit.setText("")
        self.window.passwd_line_edit.setFocus()
        self.window.main_stacked_widget.setCurrentIndex(PASSWD_PAGE)

    def cb_server_signal_emission(self, *args):
        '''Функция обратного вызова для обработки сигнала с dBus'''
        logging.info("Recieve message: %s", args)
        id = args[4][0].split(":")[1]
        self.ibutton_present.emit(id)

    def check_passwd(self):
        '''Проверить пароль'''
        try:
            # Если введен правильный пароль, остановить таймер и
            # открыть панель выбора действия Загрузка ОС/Настройки
            if self.accounts[self.auth_id]["passwd"] == self.window.passwd_line_edit.text():
                self.timer.stop()
                self.window.main_stacked_widget.setCurrentIndex(ADMIN_CHOICE_PAGE)
                return
        except KeyError as e:
            logging.info("Present unregistered iButton:", e)
        # Если введен неправильный пароль, перейти в начало
        QtWidgets.QMessageBox.warning(self, "Quit", "Неверный идентификатор или пароль", QMessageBox.Ok)
        self.ibutton_present[str].connect(self.read_auth_id)
        self.window.main_stacked_widget.setCurrentIndex(WAIT_ID_PAGE)

    def load_sys(self):
        '''Открыть панель с интерфейсом виртуальной машины'''
        try:
            # Если виртуальная машина не запущена, запустить ее
            if self.vm_state != libvirt.VIR_DOMAIN_RUNNING:
                self.dom.create()
                logging.info("ВМ %s запущена" % self.vm_name)
        except (AttributeError, libvirt.libvirtError) as e:
            logging.warning("Ошибка: %s" % e)

        self.window.main_stacked_widget.setCurrentIndex(VM_IFACE_PAGE)
        # Установить фокус на виджете, иначе не будет работать клавиатурный ввод
        self.vnc.setFocus()
        # При необходимости трекинг мыши можно отключить (здесь не отключаем)
        self.vnc.setMouseTracking(False)
        self.vnc.start()

    def closeEvent(self, e):
        logging.info("closeEvent %s" % e)

        # Если ВМ запущена спросить о принудительном выключении
        try:
            if self.vm_state == libvirt.VIR_DOMAIN_RUNNING:
                msg = QtWidgets.QMessageBox.question(
                    self, "Выход", "Принудительно выключить виртуальную машину?",
                    QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes,
                    QtWidgets.QMessageBox.No)
                if msg == QMessageBox.Yes:
                    self.dom.destroy()
            # Закрыть соединение с libvirt
            self.conn.close()
        except (AttributeError, libvirt.libvirtError) as e:
            logging.warning("Ошибка: %s" % e)

        self.vnc.stop()
        logging.info("Disconnected from VNC server")

        # Получить кортеж с элементами QRect геометрии главного окна
        geometry = self.window.geometry().getRect()
        # Преобразовать элементы кортежа в строки и разделить символом ';'
        self.config.set("window", "geometry", ";".join(map(str, geometry)))
        self.config.set("window", "state", str(int(self.window.windowState())))
        # Сохранить учетные записи пользователей
        self.config.set("general", "accounts", str(self.accounts))

        with open(self.config_file, "w") as file:
            self.config.write(file)

    def domain_event_callback(self, conn, dom, event, detail, opaque):
        '''Функция обратного вызова для обработки сообщений libvirt'''
        domain_name = dom.name()
        if event == libvirt.VIR_DOMAIN_SHUTOFF:
            logging.info("VM '%s' has shut off" % domain_name)
            self.close()
