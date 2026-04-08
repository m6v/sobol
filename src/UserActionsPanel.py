import logging
import os
import secrets
import string

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QWidget, QLineEdit, QTextEdit, QPlainTextEdit, QCheckBox, QSpinBox, QComboBox

from SobolDialog import SobolDialog


def gen_password(length=8):
    """Сгенерировать пароль заданной длины"""
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


class UserActionsPanel(QtWidgets.QMainWindow):
    """Панель мастера добавления пользователей"""
    # Сигнал завершения работы мастера
    close = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.realpath(__file__))
        # ui-файл должен иметь имя такое же как класс и храниться в каталоге ../panels
        ui_file = os.path.join(base_dir, "../panels", f"{self.__class__.__name__}.ui")

        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)

        # Регистрация дочерних виджетов в self, чтобы к ним можно было обращаться
        # не только self.ui.widget_name, а также self.widget_name
        for widget in self.ui.findChildren(QtWidgets.QWidget):
            name = widget.objectName()
            # Регистрируем только виджеты у которых есть имя и виджеты с именем,
            # начинающимся на qt_, т.к. такие имена Qt часто создает автоматически
            if not name or name.startswith("qt_"):
                continue

            if hasattr(self, name):
                # Проверить, что это не ссылка виджета на самого себя,
                # на случай, если findChildren нашел дважды из-за иерархии
                if getattr(self, name) is not widget:
                    raise AttributeError(
                        f"Attribute '{name}' already exists in {self.__class__.name__}"
                    )
            # Конфликтов имен нет, можно регистрировать виджет в self
            setattr(self, name, widget)

        self.user_name.textChanged[str].connect(self.user_name_changed)

        self.next_push_button_1.clicked.connect(self.check_user_name)
        self.yes_push_button_2.clicked.connect(self.show_next_page)

        self.passwd_line_edit.textChanged[str].connect(self.user_passwd_changed)
        self.passwd_confirm_line_edit.textChanged[str].connect(self.user_passwd_changed)

        self.next_push_button_3.clicked.connect(self.check_user_passwd)
        self.passwd_gen_push_button.clicked.connect(self.gen_user_passwd)
        self.show_passwd_radio_button.clicked.connect(self.toggle_user_passwd_visibility)

        self.cancel_push_button_1.clicked.connect(self.close)
        self.cancel_push_button_2.clicked.connect(self.close)
        self.cancel_push_button_3.clicked.connect(self.close)
        self.cancel_push_button_4.clicked.connect(self.close)
        self.finish_push_button_4.clicked.connect(self.close)

        self.stacked_widget.setCurrentIndex(0)

    def clear_all_inputs(self):
        """Очистить содержимое всех виджетов ввода"""
        for widget in self.ui.findChildren(QWidget):
            if isinstance(widget, (QLineEdit, QTextEdit, QPlainTextEdit)):
                widget.clear()
            elif isinstance(widget, QCheckBox):
                widget.setChecked(False)
            elif isinstance(widget, QSpinBox):
                widget.setValue(widget.minimum())
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)

    def show_first_page(self):
        self.clear_all_inputs()
        self.stacked_widget.setCurrentIndex(0)

    def show_next_page(self):
        """Показать следующую панель"""
        self.stacked_widget.setCurrentIndex(self.stacked_widget.currentIndex() + 1)

    def user_name_changed(self, text: str):
        """Изменить состояние кнопки "Вперед" при вводе имени нового пользователя"""
        self.next_push_button_1.setEnabled(bool(len(text)))

    def check_user_name(self):
        """Проверить уникальность имени нового пользователя"""
        logging.debug(self.user_name.text())
        # TODO Уточнить могут ли быть пользователи с одинаковыми именами или нет,
        # возможно есть ограничения на алфавит и т.п.
        # если могут исключить проверку, иначе реализовать проверку и при совпадении
        # self.user_name.text() с существуюшим пользователем выдать предупреждающее сообщение
        self.show_next_page()

    def check_user_passwd(self):
        """Проверить совпадение пароля в обоих полях ввода и его соответствие требованиям сложности"""
        if self.passwd_line_edit.text() != self.passwd_confirm_line_edit.text():
            # QtWidgets.QMessageBox.warning(self, "Ошибка", "Введенные пароли не совпадают, повторите ввод!", QtWidgets.QMessageBox.Ok)
            dialog = SobolDialog("Ошибка", "Введенные пароли не совпадают, повторите ввод!")
            dialog.exec_()
            return
        # TODO Далее нужно понять как и где считывать идентификатор iButton, как работать
        # со списком пользователей (добавляем здесь или делегируем в родительский класс)
        self.show_next_page()

    def user_passwd_changed(self, text):
        """Изменить состояние кнопки "Вперед" при наличии символов в обоих полях ввода пароля"""
        if len(self.passwd_line_edit.text()) != 0 and len(self.passwd_confirm_line_edit.text()) != 0:
            self.next_push_button_3.setEnabled(True)
        else:
            self.next_push_button_3.setEnabled(False)

    def toggle_user_passwd_visibility(self):
        """Переключить видимость пароля пользователя в полях ввода"""
        if self.show_passwd_radio_button.isChecked():
            self.passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.passwd_confirm_line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.passwd_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
            self.passwd_confirm_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)

    def gen_user_passwd(self):
        """Сгенерировать пароль пользователя и показать его в полях ввода"""
        # user_passwd = gen_password(int(self.passwd_parms_panel.min_passwd_len_line_edit.text()))
        user_passwd = gen_password()
        self.passwd_line_edit.setText(user_passwd)
        self.passwd_confirm_line_edit.setText(user_passwd)
        self.show_passwd_radio_button.setChecked(True)
        self.toggle_user_passwd_visibility()
