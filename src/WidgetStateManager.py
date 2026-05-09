import logging
from PySide2.QtWidgets import QLineEdit, QCheckBox, QComboBox, QListWidget, QWidget

from config import config


def str2bool(s):
    """Преобразовать строковое представление истины в boolean с очисткой пробелов"""
    return str(s).lower().strip() in ("y", "yes", "true", "д", "да", "1")


class WidgetStateManager:
    """Класс, обеспечивающий сохранение и восстановление состояния виджетов"""
    def save_state(self, container):
        """
        Считать значения из виджетов внутри контейнера и сохранить в config
        """
        # Использовать для названия секции objectName контейнераили имя его класса
        section = container.objectName() or container.__class__.__name__
        logging.debug(f"Save state of the {section}")

        if not config.has_section(section):
            logging.debug(f"Section {section} is created")
            config.add_section(section)

        supported_types = [QLineEdit, QCheckBox, QComboBox, QListWidget]
        widgets = []

        # Собрать виджеты по очереди для каждого типа
        for t in supported_types:
            widgets.extend(container.findChildren(t))

        for obj in widgets:
            name = obj.objectName()
            if not name:
                continue

            # Сбор данных в зависимости от типа виджета
            if isinstance(obj, QCheckBox):
                value = obj.isChecked()
            elif isinstance(obj, QLineEdit):
                value = obj.text()
            elif isinstance(obj, QComboBox):
                value = obj.currentIndex()
            elif isinstance(obj, QListWidget):
                # Множественный выбор сохраняем строкой через запятую
                indices = [str(obj.row(item)) for item in obj.selectedItems()]
                value = ",".join(indices)
            else:
                continue

            config.set(section, name, str(value))

    def load_state(self, container):
        """Загрузить значения из config и применить их к виджетам внутри контейнера"""
        section = container.objectName() or container.__class__.__name__

        if not config.has_section(section):
            logging.debug(f"Section {section} not found")
            return

        logging.debug(f"Load state of the {section}")
        for name, value in config.items(section):
            widget = container.findChild(QWidget, name)
            if not widget:
                continue
            try:
                if isinstance(widget, QCheckBox):
                    widget.setChecked(str2bool(value))
                elif isinstance(widget, QLineEdit):
                    widget.setText(value)
                elif isinstance(widget, QComboBox):
                    widget.setCurrentIndex(int(value))
                elif isinstance(widget, QListWidget):
                    widget.clearSelection()
                    try:
                        for i in value.split(","):
                            widget.item(int(i)).setSelected(True)
                    except Exception as e:
                        logging.error(f"Convertion indexes error for {name}: {e}")
            except (ValueError, TypeError) as e:
                logging.error(f"Data type error for widget '{name}': {e}")
            except Exception as e:
                logging.error(f"Couldn't restore widget '{name}': {e}")
