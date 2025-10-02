import asyncio
import binascii
import configparser
import functools
import errno
import json
import logging
import os
import socket
import subprocess
import sys
import time
import traceback

import libvirt

from PyQt5 import uic, QtWidgets
from PyQt5.Qt import QMainWindow, QAction, QThread, QCursor, QMessageBox, QRect, QFile, QDialog, QPushButton, QIcon, QVBoxLayout, QWidget, QSpacerItem, QSizePolicy, QTimer
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView
import QSwitchControl


INITIAL_DIR = CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
# Если установлена переменная окружения _MEIPASS, то запуск происходит из временного каталога,
# созданного при распаковке бандла. В этом случае путь к исходному каталогу взять из sys.executable
if hasattr(sys, "_MEIPASS"):
    INITIAL_DIR = os.path.dirname(sys.executable)

configfile = os.path.join(INITIAL_DIR, 'config.ini')

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

# Время, отводимое на вход в систему
REMAINING_TIME = 120

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        menu = QtWidgets.QMenu(parent)
        exitAction = menu.addAction("Exit")
        self.setContextMenu(menu)
        menu.triggered.connect(self.exit)

    def exit(self):
        QtCore.QCoreApplication.exit()

class MainWindow(QDialog):
	    
	# Сигнал "предъявления" iButton 
    ibutton_present = pyqtSignal(int)
	
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(CURRENT_DIR, 'MainWindow.ui'), self)

        '''
        Вариант с загрузкой формы из файла ресурсов, создаваемого с помощью pyrcc5
        stream = QFile(":MainWindow.ui")
        stream.open(QFile.ReadOnly)
        uic.loadUi(stream, self)
        stream.close()
        Не требует распространения ui-файлов вместе с приложением (только файл ресурсов)
        '''

        # Create the sidebar widget
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setFixedWidth(230)  # Set a fixed width for the sidebar
        
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
                  'user_list_panel': 'panels/EmptyPanel.ui',
                  'event_journal_panel': 'panels/EmptyPanel.ui',
                  'common_parms_panel': 'panels/CommonParmsPanel.ui',
                  'passwd_parms_panel': 'panels/PasswdParmsPanel.ui',
                  'integrity_control_panel': 'panels/IntegrityControlPanel.ui',
                  'passwd_change_panel': 'panels/EmptyPanel.ui',
                  'auth_id_change_panel': 'panels/EmptyPanel.ui',
                  'diagnostic_panel': 'panels/DiagnosticPanel.ui',
                  'service_operations_panel': 'panels/ServiceOperationsPanel.ui'
                 }
        for panel, form in panels.items():
            self.__dict__[panel] = QWidget()
            uic.loadUi(os.path.join(CURRENT_DIR, form), self.__dict__[panel])
            self.stackedWidget.addWidget(self.__dict__[panel])
            
        # Init QSystemTrayIcon
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icons/ibutton.png"))
        self.tray_icon.show()

        tray_menu = QtWidgets.QMenu()        
        for i in range(10):
            action = QAction("iButton: #%s" % i, self)
            action.triggered.connect(functools.partial(self.ibutton_action_triggered, i))
            tray_menu.addAction(action)

        self.conn = libvirt.open(None) # Открывает соединение с локальным гипервизором
        if self.conn is None:
            print('Не удалось подключиться к Libvirt')
        else:
            print('Подключение к Libvirt успешно')
        self.vm_name = "arm-abi"

        self.webEngineView = QWebEngineView()
        self.main_stacked_widget.addWidget(self.webEngineView)
        url = QUrl.fromUserInput('http://127.0.0.1:6080/vnc_lite.html?scale=true')
        self.webEngineView.load(url)
        
        # Связать сигнал и слоты    
        self.enter_push_button.clicked.connect(self.check_passwd)
        
        self.tray_icon.setContextMenu(tray_menu)

        # Словарь, ключи которого - идентификатор iButton, значения - сведения об учетной записи
        self.accounts = {0: "Aa123456", 1: "12345678"}
        
        # Оставшееся до входа в систему время, отображаемое в первых двух окнах
        self.remaining_time = REMAINING_TIME
        self.timer = QTimer();
        self.timer.timeout.connect(self.decrease_remaining_time)
        self.timer.start(1000)

        self.auth_id = 0
        # Показать нулевую страницу и ждать "прикладывания" iButton
        self.ibutton_present[int].connect(self.wait_auth_id)
        self.main_stacked_widget.setCurrentIndex(0)
        
    def menu_action_triggered(self, index):
        self.stackedWidget.setCurrentIndex(index)
        # При необходимости скрыть панель меню вызвать метод self.sidebar_widget.hide()
        
    def ibutton_action_triggered(self, index):
        self.ibutton_present.emit(index)

    def decrease_remaining_time(self):
        self.remaining_time -= 1
        if self.remaining_time == 0:
            self.remaining_time = REMAINING_TIME
            self.ibutton_present[int].connect(self.wait_auth_id)
            self.main_stacked_widget.setCurrentIndex(0)
        else:
            # TODO Перевести секунды в минуты и секунды
            self.remaining_time_value_label.setText("%s сек." % self.remaining_time)

    def wait_auth_id(self, auth_id):
        print('iButton %i present' % auth_id)
        self.auth_id = auth_id
        # Отключаем обработчик "прикладывания" iButton
        self.ibutton_present[int].disconnect()
        self.id_label.setText("iButton %i" % self.auth_id)
        self.main_stacked_widget.setCurrentIndex(1)

    def check_passwd(self):
        self.remaining_time = REMAINING_TIME
        # Проверить пароль
        try:
            if self.accounts[self.auth_id] == self.passwd_line_edit.text():
                self.timer.stop()
                
                ######### ЗАПУСК ВМ ########
                try:
                    vm = self.conn.lookupByName(self.vm_name)
                    if vm.state() != libvirt.VIR_DOMAIN_RUNNING:
                        vm.create() # Запуск
                        print(f"ВМ '{self.vm_name}' запущена")
                except libvirt.libvirtError as e:
                    print(f"Ошибка: {e}")
                ############################
                self.webEngineView.reload()
                self.main_stacked_widget.setCurrentIndex(3)
                
                return
        except KeyError as e:
            print("Present unregistered iButton:", e)
        # Если введен неправильный пароль,перейти в нулевое окно
        QtWidgets.QMessageBox.warning(self, 'Quit', 'Неверный идентификатор или пароль ',  QMessageBox.Ok)
        self.ibutton_present[int].connect(self.wait_auth_id)
        self.main_stacked_widget.setCurrentIndex(0)
