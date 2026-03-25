import sys
import csv
from datetime import datetime

from PySide2.QtWidgets import QApplication, QMainWindow, QTableView
from PySide2.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel

from constants import EVENTS_TYPE

class CsvTableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._headers = headers
        self._data = data
        # Если нужна предобработка данных, то self._data = self.parse_data(data)

    def parse_data(self, data):
        """Метод предобработки исходных данных"""
        parsed = []

        for row in data:
            # Дата и время события
            try:
                dt = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                event_time = dt.strftime("%H:%M:%S")
                event_date = dt.strftime("%d.%m.%Y")
            except Exception:
                event_time = "Неизвестно"
                event_date = "Неизвестно"

            # Тип событий
            evevt_type = EVENTS_TYPE[int(row[3])]

            # Статус событий
            status_raw = row[4]
            if status_raw == "1":
                event_status = "Успех"
            elif status_raw == "0":
                event_status = "Ошибка"
            else:
                event_status = "Неизвестно"

            parsed.append([event_time, event_date] + row[1:3] + [evevt_type] + [event_status])

        return parsed

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


class DateTimeFilterProxy(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.date_from = None
        self.date_to = None
        self.status_filter = None

    def setRange(self, date_from, date_to):
        self.date_from = date_from
        self.date_to = date_to
        self.invalidateFilter()

    def setStatusFilter(self, status):
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
