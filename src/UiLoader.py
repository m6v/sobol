from PySide2 import QtCore, QtUiTools

class UiLoader(QtUiTools.QUiLoader):
    """Класс, позволяющий загружать пользовательский интерфейс в виджет
    верхнего уровня, а не в переменную, как это выполняет "классический" QUiLoader"""
    _baseinstance = None

    def createWidget(self, classname, parent=None, name=''):
        if parent is None and self._baseinstance is not None:
            widget = self._baseinstance
        else:
            widget = super().createWidget(classname, parent, name)
            if self._baseinstance is not None:
                setattr(self._baseinstance, name, widget)
        return widget

    def loadUi(self, uifile, baseinstance=None):
        self._baseinstance = baseinstance
        widget = self.load(uifile)
        QtCore.QMetaObject.connectSlotsByName(baseinstance)
        return widget
