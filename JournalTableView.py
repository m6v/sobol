import sys
import csv
from datetime import datetime

from PySide2.QtWidgets import QApplication, QMainWindow, QTableView
from PySide2.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel, QModelIndex

from constants import EVENTS_TYPE

class JournalTableModel(QAbstractTableModel):
    def __init__(self, journal_file):
        super().__init__()
        self._journal_file = journal_file
        self._headers = ["Время", "Пользователь", "Номер ЭИ", "Описание", "Статус"]

        with open(self._journal_file, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            data = list(reader)

        self._data = data

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
         
        value = self._data[index.row()][index.column()]

        if role == Qt.DisplayRole:
            if index.column() == 3:
                return EVENTS_TYPE[int(value)]
            if index.column() == 4:
                if value == "1":
                    return "Успех"
                else:
                    return "Ошибка"

            return str(value)

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self._headers[section]
        else:
            return str(section + 1)
            
    def add_event(self, event):
        """Добавить событие в журнал"""
        row = len(self._data)
        self.beginInsertRows(QModelIndex(), row, row)
        # Первым элементом всегда добавляем текущее время
        self._data.append([datetime.now().strftime("%H:%M %d/%m/%Y")] + event)
        self.endInsertRows()
        
    def save(self):
        with open(self._journal_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerows(self._data)


class JournalProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.date_from = None
        self.date_to = None
        self.status_filter = None

    def setDateTimeFilter(self, date_from=None, date_to=None):
        self.date_from = date_from
        self.date_to = date_to
        self.invalidateFilter()

    def setStatusFilter(self, status=None):
        self.status_filter = status
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        """Метод должен вернуть true, если элемент в строке source_row и источнике source_parent должен быть включен в модель"""
        model = self.sourceModel()

        dt = model._data[source_row][0]
        status = model._data[source_row][-1]

        # Пример фильтра по дате
        if dt is None:
            return False

        if self.date_from and dt < self.date_from:
            return False

        if self.date_to and dt > self.date_to:
            return False

        # Пример фильтра по статусу события
        if self.status_filter is not None and status != self.status_filter:
            return False

        return True
