from PySide2 import QtCore, QtUiTools


class UiLoader(QtUiTools.QUiLoader):
    """Класс, позволяющий загружать пользовательский интерфейс в виджет
    верхнего уровня, а не в переменную, как это выполняет "классический" QUiLoader"""
    def __init__(self, baseinstance=None, *custom_widgets):
        super().__init__(baseinstance)
        self._baseinstance = baseinstance
        # Регистрируем кастомные виджеты, если они переданы
        for widget_class in custom_widgets:
            self.registerCustomWidget(widget_class)

    def createWidget(self, classname, parent=None, name=''):
        # Если это корневой виджет
        if parent is None and self._baseinstance is not None:
            return self._baseinstance

        # Создаем дочерний виджет
        widget = super().createWidget(classname, parent, name)

        # Привязываем его к нашему классу, только если задано имя в Designer
        if self._baseinstance is not None and name:
            setattr(self._baseinstance, name, widget)
        return widget

    @classmethod
    def loadUi(cls, uifile, baseinstance, custom_widgets=None):
        loader = cls(baseinstance, custom_widgets)
        ui_file = QtCore.QFile(uifile)
        ui_file.open(QtCore.QFile.ReadOnly)
        widget = loader.load(ui_file)
        ui_file.close()
        QtCore.QMetaObject.connectSlotsByName(baseinstance)
        return widget
