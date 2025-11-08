1. Убрать функционал WebEngine и откатиться обратно на PyQt
2. При переходе между панелями переустанавливать настройки элементов из сохраненных!
2. Убрать из списка пользователей Администратора, т.к. для него не хранятся имя, настройки, его не надо выводить в списке пользователей. Вместо этого можно добавить параметр admin с необходимыми параметрами!
2. Разобраться почему в панели настроек пользователей на кнопках не отображаются иконки (ошибок не выдается)
3. Сделать класс со списком пользователей UserList и их настройками. Методы remove_user(user), remove_all_users(), add_user(user), get_user(user_id)
4. В настройках хранить не учетные записи, а идентификаторы зарегистрированных iButton. Данные об учетках хранить в настройках ibutton2dbus и передавать через dbus
5. Разобраться с ошибками при множественном наследовании QVNCWidget(QWidget, RFBClient). В PyQt5 работает нормально, а в PySide2 нет! В итоге пришлось вставлять костыли и сейчас хотя и работает, но выдает ошибки
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
5. Когда будет "Соболь" разобраться, что происходит при нажатии кнопок "Отмена" на панелях настроек (значения элементов возвращаются к предыдущим или остаются текущими, просто не записываются в память устройства)
6. При закрытии окна отображается сообщение "Release of profile requested but WebEnginePage still not deleted. Expect troubles !". Видимо нужно отлавилвать close event и корректно завершать приложение с закрытием WebEngine
