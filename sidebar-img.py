#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Sidebar with Background Image")
        self.setGeometry(100, 100, 1800, 1200)

        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create a main layout for the central widget
        main_layout = QVBoxLayout(central_widget)

        # Create the sidebar widget
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setFixedWidth(230)  # Set a fixed width for the sidebar
        
        # Apply background image using QSS
        self.sidebar_widget.setStyleSheet("""
            QWidget {
                font: 8pt 'Monospace Regular';
                background-image: url(background.png);
                background-repeat: no-repeat;
                background-position: up;
                background-color: #48A23F;
            }
            QPushButton {
                background-color: #48A23F;
                width: 75px ;
                height: 50px;
                border: none;
                text-align: left;
                padding: 0px 0px 0px 20px;
                color: white;
           }
           QPushButton:hover {
                background: #3D8A36; 
           }            
           QPushButton:pressed {
                background-color: #3D8A36;
           }
        """)
        # background-size: cover; /* or 'contain' or specific dimensions like '100% 100%' */

        # Create a layout for the sidebar and add some content
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Кастомный класс кнопок с выравниванием и отступами
        # https://www.xingyulei.com/post/qt-button-alignment/index.html

        buttons = {"Загрузка ОС": "load_os.png",
                   "Режим работы": "mode.png",
                   "Список пользователей": "users.png",
                   "Журнал событий": "journal.png",
                   "Общие параметры": "common_parms.png",
                   "Параметры паролей": "passwd_parms.png",
                   "Контроль целостности": "integrity_control.png",
                   "Смена пароля": "passwd_change.png",
                   "Смена аутентификатора": "auth_change.png",
                   "Диагностика платы": "diagnostic.png",
                   "Служебные операции": "service_operations.png"
                   
				  }
        for name, icon in buttons.items():
            print(name, icon)
            button = QPushButton(name)
            button.setIcon(QIcon(icon))
            sidebar_layout.addWidget(button)
        '''
        load_os = QPushButton("Загрузка ОС")
        load_os.setIcon(QIcon('/home/m6v/Workspace/load_os.png'))
        sidebar_layout.addWidget(load_os)
        sidebar_layout.addWidget(QPushButton("Режим работы"))
        sidebar_layout.addWidget(QPushButton("Список пользователей"))
        '''
        sidebar_layout.addStretch() # Pushes buttons to the top

        # Add the sidebar to the main layout
        main_layout.addWidget(self.sidebar_widget, alignment=Qt.AlignLeft)

        # Add other content to the main window (e.g., a main content area)
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: lightgray;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.addWidget(QPushButton("Main Content Button"))
        main_layout.addWidget(content_widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
