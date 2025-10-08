import configparser
import functools
import json
import logging
import os
import sys

import libvirt

from PyQt5 import uic, QtWidgets
from PyQt5.Qt import QMainWindow, QMessageBox, QRect, QPushButton, QIcon, QVBoxLayout, QWidget, QSpacerItem, QSizePolicy, QTimer, QLineEdit, QImage, QSize, QPalette, QBrush
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView

from pydbus import SessionBus
from gi.repository import GLib

loop = GLib.MainLoop()
dbus_filter = "/com/example/MyService"
bus = SessionBus()

INITIAL_DIR = CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
# Если установлена переменная окружения _MEIPASS, программа запущена
# из временного каталога, созданного при распаковке бандла
if hasattr(sys, "_MEIPASS"):
    # Путь к временному каталогу взять из sys.executable
    INITIAL_DIR = os.path.dirname(sys.executable)

configfile = os.path.join(INITIAL_DIR, 'config.ini')

# Для логирования в файл, добавить filename='app.log' иначе лог в консоль
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

# Время, отводимое на вход в систему
REMAINING_TIME = 120

# Индексы панелей
AUTH_ID_PAGE = 0
PASSWD_PAGE = 1
ADMIN_ACTION_PAGE = 2
SETTINGS_PAGE = 3
VM_VIEW_PAGE = 4


class MainWindow(QMainWindow):
    # Сигнал "предъявления" iButton
    ibutton_present = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(CURRENT_DIR, 'TestWindow.ui'), self)

        '''
        Вариант с загрузкой формы из файла ресурсов, создаваемого с помощью pyrcc5
        stream = QFile(":MainWindow.ui")
        stream.open(QFile.ReadOnly)
        uic.loadUi(stream, self)
        stream.close()
        Не требует распространения ui-файлов вместе с приложением (только файл ресурсов)
        '''

        self.config = configparser.ConfigParser(allow_no_value=True)
        # Установить чувствительность ключей к регистру
        self.config.optionxform = str
        self.config.read(configfile)

        try:
            # Словарь, ключи которого - идентификатор iButton, значения - сведения об учетной записи (пароль, имя и др.)
            self.accounts = eval(self.config.get("general", "accounts"))
            # Имя виртуальной машины
            self.vm_name = self.config.get("general", "vm_name")

            # Разбить строку на элементы, преобразовать их в целые числа и получить QRect с геометрией главного окна
            geometry = QRect(*map(int, self.config.get('window', 'geometry').split(';')))
            # Восстановить геометрию главного окна
            self.setGeometry(geometry)

            state = int(self.config.get('window', 'state'))
            self.restoreState(bytearray(state))
        except configparser.NoOptionError as e:
            logging.warning(e)

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
        self.mainHorizontalLayout.insertWidget(0, self.sidebar_widget, alignment=Qt.AlignLeft)

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
        for panel, form in panels.items():
            self.__dict__[panel] = QWidget()
            uic.loadUi(os.path.join(CURRENT_DIR, form), self.__dict__[panel])
            self.stackedWidget.addWidget(self.__dict__[panel])

        # Register the default event implementation
        libvirt.virEventRegisterDefaultImpl()
        # Открыть соединение с локальным гипервизором
        self.conn = libvirt.open(None)
        if self.conn is None:
            logging.warning("Не удалось подключиться к libvirt")
        else:
            logging.info("Подключение к libvirt успешно")

        self.dom = self.conn.lookupByName(self.vm_name)

        # Зарегистрировать функцию обратного вызова для обработки событий от libvirt для всех доменов
        self.conn.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE, self.domain_event_callback, None)
        # Проверить нужна команда или нет?!
        libvirt.virEventRunDefaultImpl()

        # На рабочем копьютере попатка использования QWebEngineView
        # приводит к ошибке "Could not find QtWebEngineProcess"!
        '''
        self.webEngineView = QWebEngineView()
        self.main_stacked_widget.addWidget(self.webEngineView)
        url = QUrl.fromUserInput("http://127.0.0.1:6080/vnc_lite.html?scale=true")
        self.webEngineView.load(url)
        '''

        # Установка свойства в форме почему-то не работает?!
        self.passwd_line_edit.setEchoMode(QLineEdit.Password)

        # Связать сигнал и слоты
        self.enter_push_button.clicked.connect(self.check_passwd)
        self.passwd_line_edit.returnPressed.connect(self.check_passwd)
        self.go_settings_push_button.clicked.connect(functools.partial(self.main_stacked_widget.setCurrentIndex, SETTINGS_PAGE))
        self.load_sys_push_button.clicked.connect(self.load_sys)
        self.sys_load_panel.load_sys_push_button.clicked.connect(self.load_sys)

        # Идентификатор считанной iButton
        self.auth_id = ""

        # Оставшееся до входа в систему время, отображаемое в первых двух окнах
        self.remaining_time = REMAINING_TIME
        self.timer = QTimer()
        self.timer.timeout.connect(self.decrease_remaining_time)
        
        # Подписаться на получение сигналов с шины bus и
        # установить функцию обратного вызова для обработки сигнала
        bus.subscribe(object=dbus_filter, signal_fired=self.cb_server_signal_emission)

        state, reason = self.dom.state()
        logging.info("Domain %s state: %s, reason: %s" % (self.dom.name(), state, reason))
        if state == libvirt.VIR_DOMAIN_RUNNING:
            # ВМ уже запущена, поэтому открываем панели с ее интерфейсом
            logging.info("%s is running" % self.vm_name)
            self.main_stacked_widget.setCurrentIndex(VM_VIEW_PAGE)
        else:
            # ВМ не запущена, поэтому ждать "прикладывания" iButton
            logging.info("%s is't running" % self.vm_name)
            self.main_stacked_widget.setCurrentIndex(AUTH_ID_PAGE)
            self.ibutton_present[str].connect(self.wait_auth_id)
            self.timer.start(1000)

    def menu_action_triggered(self, index):
        self.stackedWidget.setCurrentIndex(index)
        # При необходимости скрыть панель меню вызвать метод self.sidebar_widget.hide()

    def decrease_remaining_time(self):
        self.remaining_time -= 1
        if self.remaining_time == 0:
            self.remaining_time = REMAINING_TIME
            self.ibutton_present[str].connect(self.wait_auth_id)
            self.main_stacked_widget.setCurrentIndex(AUTH_ID_PAGE)
        else:
            # TODO Перевести секунды в минуты и секунды
            self.remaining_time_label_1.setText("До окончания входа в систему осталось: %s сек." % self.remaining_time)
            self.remaining_time_label_2.setText("До окончания входа в систему осталось: %s сек." % self.remaining_time)

    def wait_auth_id(self, auth_id):
        logging.info("iButton %s is presented" % auth_id)
        self.auth_id = auth_id
        # Отключаем обработчик "прикладывания" iButton
        self.ibutton_present[str].disconnect()
        self.id_label.setText("iButton %s" % self.auth_id)
        # Стереть поле ввода пароля на случай, если выполняем попытку повторного ввода
        self.passwd_line_edit.setText("")
        self.passwd_line_edit.setFocus()
        self.main_stacked_widget.setCurrentIndex(PASSWD_PAGE)

    def cb_server_signal_emission(self, *args):
        '''Функция обратного вызова для обработки сигнала с dBus'''
        logging.info("Recieve message: %s", args)
        id = args[4][0].split(":")[1]
        self.ibutton_present.emit(id)

    def check_passwd(self):
        '''Проверка пароля'''
        try:
            # Если введен правильный пароль, остановить таймер и
            # открыть панель выбора действия Загрузка ОС/Настройки
            if self.accounts[self.auth_id]["passwd"] == self.passwd_line_edit.text():
                self.timer.stop()
                self.main_stacked_widget.setCurrentIndex(ADMIN_ACTION_PAGE)
                return
        except KeyError as e:
            logging.info("Present unregistered iButton:", e)
        # Если введен неправильный пароль, перейти в начало
        QtWidgets.QMessageBox.warning(self, "Quit", "Неверный идентификатор или пароль", QMessageBox.Ok)
        self.ibutton_present[str].connect(self.wait_auth_id)
        self.main_stacked_widget.setCurrentIndex(AUTH_ID_PAGE)

    def load_sys(self):
        '''Запустить виртуальную машину self.vm_name'''
        try:
            if self.dom.state() != libvirt.VIR_DOMAIN_RUNNING:
                self.dom.create()
                logging.info("ВМ %s запущена" % self.vm_name)
        except libvirt.libvirtError as e:
            logging.warning("Ошибка: %s" % e)

        # На рабочем копьютере попатка использования QWebEngineView
        # приводит к ошибке "Could not find QtWebEngineProcess"!
        '''
        self.webEngineView.reload()
        self.main_stacked_widget.setCurrentIndex(VM_VIEW_PAGE)
        '''

    def closeEvent(self, e):
        # Если ВМ запущена спросить о принудительном выключении
        if self.dom.state()[0] == libvirt.VIR_DOMAIN_RUNNING:
            msg = QtWidgets.QMessageBox.question(self, "Выход", "Принудительно выключить виртуальную машину?",
                                                 QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes,
                                                 QtWidgets.QMessageBox.No)
            if msg == QMessageBox.Yes:
                self.dom.destroy()
        # Закрыть соединение с libvirt
        self.conn.close()

        # Получить кортеж с элементами QRect геометрии главного окна
        geometry = self.geometry().getRect()
        # Преобразовать элементы кортежа в строки и разделить символом ';'
        self.config.set("window", "geometry", ";".join(map(str, geometry)))
        self.config.set("window", "state", str(int(self.windowState())))
        # Сохранить учетные записи пользователей
        self.config.set("general", "accounts", str(self.accounts))
        
        with open(configfile, "w") as file:
            self.config.write(file)

    def domain_event_callback(self, conn, dom, event, detail, opaque):
        """Функция обратного вызова для обработки сообщений libvirt"""
        domain_name = dom.name()
        if event == libvirt.VIR_DOMAIN_SHUTOFF:
            logging.info("VM '%s' has shut off" % domain_name)
            self.close()
