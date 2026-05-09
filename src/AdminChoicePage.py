from datetime import datetime
import logging

from PySide2.QtCore import Qt
from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QPalette, QImage, QBrush, QShowEvent

from config import config
from UiLoader import UiLoader


class AdminChoicePage(QtWidgets.QWidget):
    """Страница выбора действий администратора (Загрузка ОС или Настройки)"""
    sys_load_requested = QtCore.Signal()
    show_settings_requested = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAutoFillBackground(True)

        self.loader = UiLoader()
        self.loader.loadUi("../ui/AdminChoicePage.ui", self)

        self.setStyleSheet("""
            QPushButton { border: 2px solid white; color: white; }
            QLabel { color: white; }
            """)

        self.sys_load_push_button.clicked.connect(self.sys_load_requested.emit)
        self.show_settings_push_button.clicked.connect(self.show_settings_requested.emit)

    def resizeEvent(self, event):
        palette = QPalette()
        img = QImage("../img/background.png")
        # Если нужно сохранять пропорции, то вместо IgnoreAspectRatio
        # использовать KeepAspectRatioByExpanding
        scaled = img.scaled(self.size(), Qt.IgnoreAspectRatio)
        palette.setBrush(QPalette.Window, QBrush(scaled))
        self.setPalette(palette)

    def on_ibutton_present(self, message):
        logging.debug(message)

    def showEvent(self, event: QShowEvent):
        # Если ни один пользователь не зарегистрирован, пропустить вывод сведений о последнем входе в систему
        if config.users:
            # Найти пользователя входившего в систему последним
            last_user = config.users[0]
            for user in config.users:
                if datetime.strptime(user["last_login_datetime"], "%H:%M %Y/%m/%d") > datetime.strptime(last_user["last_login_datetime"], "%H:%M %Y/%m/%d"):
                    last_user = user

            self.last_user_name_value.setText(last_user["user_name"])
            self.last_user_id_value.setText(last_user["id"])
            self.last_user_datetime_value.setText(last_user["last_login_datetime"])

        self.failed_logins_value.setText(str(config.failed_logins))
        self.admin_datetime_value.setText(datetime.now().strftime("%H:%M %Y/%m/%d"))
        super().showEvent(event)
