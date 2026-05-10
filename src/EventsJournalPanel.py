from datetime import datetime
import logging
from pathlib import Path

from PySide2 import QtCore, QtGui, QtWidgets

from config import config
from Toggle import Toggle
from UiLoader import UiLoader

from constants import EVENTS_TYPE

from WidgetStateManager import WidgetStateManager
from JournalTableView import JournalTableModel, JournalProxyModel

VIEW_JOURNAL_PAGE = 0
EXPORT_JOURNAL_PAGE = 1
PARMS_JOURNAL_PAGE = 2
SEARCH_JOURNAL_PAGE = 3


class EventsJournalPanel(QtWidgets.QWidget):
    """Панель просмотра журнала событий"""
    # Сигнал завершения работы мастера
    close = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__()

        self.loader = UiLoader()
        # Загружаем интерфейс и регистрируем кастомный класс Toggle
        self.loader.loadUi("../ui/EventsJournalPanel.ui", self, Toggle)
        self.setObjectName("events_journal_panel")

        # Заполнить таблицу фильтрации событий по типу
        for item in EVENTS_TYPE.values():
            self.events_type_list_widget.addItem(item)

        self.widget_state_manager = WidgetStateManager()
        self.widget_state_manager.load_state(self)
        # Установить состояние списка событий в зависимости от переключателя "Поик по типу событий"
        self.events_type_list_widget.setEnabled(self.events_type_search_check_box.isChecked())

        # Если файла журнала нет, то создать его
        Path.touch(config.journal_file)
        self.model = JournalTableModel(config.journal_file)

        self.proxy_model = JournalProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.journal_table_view.setModel(self.proxy_model)

        datetime_regex = QtCore.QRegExp(
            r"([01][0-9]|2[0-3]):([0-5][0-9])\s"
            r"(0[1-9]|[12][0-9]|3[01])/"
            r"(0[1-9]|1[0-2])/"
            r"(\d{4})"
        )
        validator = QtGui.QRegExpValidator(datetime_regex)
        self.events_start_time_line_edit.setValidator(validator)
        self.events_end_time_line_edit.setValidator(validator)

        journal_size_regex = QtCore.QRegExp(r"(1000|[1-9]\d{2})")
        validator = QtGui.QRegExpValidator(journal_size_regex)
        self.journal_max_size_line_edit.setValidator(validator)

        self.view_journal_push_button.clicked.connect(lambda: self.show_journal_panel(VIEW_JOURNAL_PAGE))
        self.export_journal_push_button.clicked.connect(lambda: self.show_journal_panel(EXPORT_JOURNAL_PAGE))
        self.parms_journal_push_button.clicked.connect(lambda: self.show_journal_panel(PARMS_JOURNAL_PAGE))
        self.search_journal_push_button.clicked.connect(lambda: self.show_journal_panel(SEARCH_JOURNAL_PAGE))
        self.select_parms_push_button.clicked.connect(self.apply_event_filter)
        self.cancel_parms_push_button.clicked.connect(self.cancel_event_filter)
        self.select_all_push_button.clicked.connect(self.events_type_list_widget.selectAll)
        self.clear_all_push_button.clicked.connect(self.events_type_list_widget.clearSelection)
        self.save_push_button.clicked.connect(self.save_panel_settings)
        self.events_type_search_check_box.clicked.connect(self.trigger_events_type_search)
        self.events_time_search_check_box.clicked.connect(self.trigger_events_type_search)

        self.show_journal_panel(VIEW_JOURNAL_PAGE)

    def clear_all_inputs(self):
        """Очистить содержимое всех виджетов ввода"""
        for widget in self.findChildren(QtWidgets.QWidget):
            if isinstance(widget, (QtWidgets.QLineEdit, QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit)):
                widget.clear()
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(False)
            elif isinstance(widget, QtWidgets.QSpinBox):
                widget.setValue(widget.minimum())
            elif isinstance(widget, QtWidgets.QComboBox):
                widget.setCurrentIndex(0)

    def show_journal_panel(self, index):
        """Показать выбранную панель журнала событий"""
        self.journal_stacked_widget.setCurrentIndex(index)

    def apply_event_filter(self):
        """Приметить выбранные фильтры журнала событий"""
        if self.events_time_search_check_box.isChecked():
            try:
                date_from = datetime.strptime(self.events_start_time_line_edit.text(), "%H:%M %d/%m/%Y")
                date_to = datetime.strptime(self.events_end_time_line_edit.text(), "%H:%M %d/%m/%Y")
                self.proxy_model.setDateTimeFilter(date_from, date_to)
            except ValueError as e:
                # TODO Показать диалоговое окно с ошибкой формата даты и времени
                logging.error(e)
        else:
            self.proxy_model.setDateTimeFilter()

        if self.events_type_search_check_box.isChecked():
            self.event_type_filter = [
                self.events_type_list_widget.row(item)
                for item in self.events_type_list_widget.selectedItems()
            ]
            self.proxy_model.setTypeFilter(self.event_type_filter)
        else:
            self.proxy_model.setTypeFilter(None)
        # Сохранить фильтры событий и переключиться на панель поиска
        self.save_panel_settings()
        self.show_journal_panel(VIEW_JOURNAL_PAGE)

    def cancel_event_filter(self):
        """Отметить выбранные фильтры журнала событий"""
        logging.debug("Cancel datetime filter")
        self.proxy_model.setDateTimeFilter()
        self.proxy_model.setTypeFilter()
        self.show_journal_panel(0)

    def trigger_events_type_search(self):
        """Изменить состояние элементов управления фильтрации событий по типам"""
        self.events_type_list_widget.setEnabled(self.events_type_search_check_box.isChecked())
        self.select_all_push_button.setEnabled(self.events_type_search_check_box.isChecked())
        self.clear_all_push_button.setEnabled(self.events_type_search_check_box.isChecked())

    def add_event(self, event):
        """Добавить событие в журнал"""
        self.model.add_event(event)

    def save_panel_settings(self):
        self.widget_state_manager.save_state(self)
