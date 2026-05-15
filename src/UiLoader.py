import xml.etree.ElementTree as ET
from PySide2 import QtCore, QtUiTools
from PySide2.QtWidgets import (QWidget, QLineEdit, QCheckBox, QPushButton, QRadioButton,
                               QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit)

class UiLoader(QtUiTools.QUiLoader):
    """Класс, позволяющий загружать пользовательский интерфейс в виджет
    верхнего уровня и автоматически восстанавливать его дефолтные значения"""
    
    def __init__(self, baseinstance=None):
        super().__init__(baseinstance)
        self._baseinstance = baseinstance
        self._ui_root = None 

    def createWidget(self, classname, parent=None, name=''):
        if parent is None and self._baseinstance is not None:
            return self._baseinstance

        widget = super().createWidget(classname, parent, name)
        if widget is None:
            return None

        if self._baseinstance is not None and name:
            setattr(self._baseinstance, name, widget)
        return widget

    @classmethod
    def loadUi(cls, uifile, baseinstance, custom_widgets=None):
        """Загрузить ui-файл, зарегистрировать кастомные виджеты и кэшировать XML-структуру"""
        loader = cls(baseinstance)
        baseinstance._ui_loader = loader 
        
        # Зарегистрировать кастомные виджеты, если они переданы
        if custom_widgets is not None:
            # Если передан один класс, а не список, превратить его в список
            if not isinstance(custom_widgets, (list, tuple)):
                custom_widgets = [custom_widgets]
                
            for widget_class in custom_widgets:
                if widget_class is not None:
                    loader.registerCustomWidget(widget_class)
        
        # Кэшировать XML-структуру для последующих сбросов
        loader._ui_root = ET.parse(uifile).getroot()
        
        # Загрузить интерфейс
        ui_file = QtCore.QFile(uifile)
        ui_file.open(QtCore.QFile.ReadOnly)
        widget = loader.load(ui_file)
        ui_file.close()
        
        QtCore.QMetaObject.connectSlotsByName(baseinstance)
        return widget

    def restore_defaults(self):
        """Автоматически сбросить все дочерние виджеты к дефолтам из XML"""
        if self._baseinstance is None or self._ui_root is None:
            return

        # Принудительно сбросить все элементы до базового состояния Qt
        for widget in self._baseinstance.findChildren(QtCore.QObject):
            if isinstance(widget, QWidget):
                widget.setEnabled(True)

            if isinstance(widget, (QLineEdit, QTextEdit)):
                widget.clear()
            elif isinstance(widget, (QCheckBox, QRadioButton)):
                widget.setChecked(False)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                if hasattr(widget, 'setMinimum'):
                    widget.setValue(widget.minimum())
                else:
                    widget.setValue(0)
            elif isinstance(widget, QComboBox):
                if widget.count() > 0:
                    widget.setCurrentIndex(0)
        
        # Применить конфигурацию, сохраненную в ui-файле
        for widget_node in self._ui_root.findall(".//widget"):
            name = widget_node.get("name")
            if not name:
                continue
                
            child_widget = self._baseinstance.findChild(QtCore.QObject, name)
            if not child_widget:
                continue
                
            for prop in widget_node.findall("./property"):
                prop_name = prop.get("name")
                self._apply_property(child_widget, prop_name, prop)

    def _apply_property(self, widget, prop_name, prop_node):
        """Маппить свойства XML на методы PySide2"""
        if prop_name == "enabled":
            node = prop_node.find("bool")
            if node is not None and hasattr(widget, "setEnabled"):
                widget.setEnabled(node.text.lower() == "true")

        elif prop_name == "text":
            # Исключить переименование QPushButton
            if isinstance(widget, QPushButton):
                return
            node = prop_node.find("string")
            if node is not None and hasattr(widget, "setText"):
                widget.setText(node.text if node.text is not None else "")

        elif prop_name == "checked":
            node = prop_node.find("bool")
            if node is not None and hasattr(widget, "setChecked"):
                widget.setChecked(node.text.lower() == "true")

        elif prop_name in ("value", "minimum", "maximum"):
            node = prop_node.find("number")
            if node is not None:
                try:
                    val = int(node.text)
                except ValueError:
                    val = float(node.text)
                setter_name = f"set{prop_name.capitalize()}"
                if hasattr(widget, setter_name):
                    getattr(widget, setter_name)(val)
                    
        elif prop_name == "currentIndex":
            node = prop_node.find("number")
            if node is not None and hasattr(widget, "setCurrentIndex"):
                widget.setCurrentIndex(int(node.text))
