1. Разобраться почему в панели настроек пользователей на кнопках не отображаются иконки (ошибок не выдается)
2. Настройках хранить не учетные записи, а идентификаторы зарегистрированных iButton. Данные об учетках хранить в настройках ibutton2dbus и передавать через dbus
3. Разобраться с ошибками при множественном наследовании QVNCWidget(QWidget, RFBClient). В PyQt5 работает нормально, а в PySide2 нет! В итоге пришлось вставлять костыли и сейчас хотя и работает, но выдает ошибки
Traceback (most recent call last):
  File "/home/m6v/Workspace/sobol/MainWindow.py", line 290, in eventFilter
    self.closeEvent(event)
  File "/home/m6v/Workspace/sobol/MainWindow.py", line 415, in closeEvent
    self.vnc.stop()
  File "/home/m6v/Workspace/sobol/qvncwidget/qvncwidget.py", line 74, in stop
    self.closeConnection()
  File "/home/m6v/Workspace/sobol/qvncwidget/rfb.py", line 429, in closeConnection
    self.__close()
  File "/home/m6v/Workspace/sobol/qvncwidget/rfb.py", line 119, in __close
    if self.connection:
AttributeError: 'QVNCWidget' object has no attribute 'connection'
Release of profile requested but WebEnginePage still not deleted. Expect troubles !
4. Когда будет "Соболь" разобраться, что происходит при нажатии кнопок "Отмена" на панелях настроек (значения элементов возвращаются к предыдущим или остаются текущими, просто не записываются в память устройства)

