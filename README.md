# sobol
Имитатор программно-аппаратного комплекса "Соболь"

До запуска программы запустить
- ibutton2dbus (эмулятор чтения iButton, передающий идентификатор в сессионную dbus)
- websockify  6080 127.0.0.1:5901 --web /usr/share/novnc

##
Зависимости:
- python3-pyqt5 (если по дефолту не установлен)
- python3-pyqt5.qtwebengine
- python3-pydbus
- python3-libvirt
- novnc
- python3-websockify (если по дефолту не установлен или не ставится с novnc)

Создаем виртуальное окружение
python3 -m venv sobol_env
активируем его
source sobol_env/bin/activate
Перед установкой в вируальном окружении можно посмотреть какие версии пакетов предусмотрены для системы пытаться установить их
В виртуальном окружении установить
$python3 -m pip install PyQt5==5.15.7 (дефолтная версия PyQt5-5.15.11 при установке выдает ошибку)
                                   PyQtWebEngine==5.14.0
                                   libvirt-python==6.1.0 (предварительно в системе нужно поставить пакет libvirt-dev)
                                   pydbus==0.6.0
                                   PyGObject==3.36.0 (требует установки в системе libcairo2-dev, libgirepository1.0-dev)

$pip list
Package        Version
-------------- -------
libvirt-python 6.1.0  
pip            20.0.2 
pkg-resources  0.0.0  
pycairo        1.26.1 
pydbus         0.6.0  
pygobject      3.36.0 
PyQt5          5.15.7 
PyQt5-Qt5      5.15.17
PyQt5-sip      12.15.0
PyQtWebEngine  5.14.0 
setuptools     44.0.0 

На рабочем копьютере команда
self.webEngineView.load(url)
приводит к ошибке "Could not find QtWebEngineProcess"
Сам бинарник находится в каталоге /usr/lib/x86_64-linux-gnu/qt5/libexec/
Скорее всего конфликт версий, установленных в виртуальном окружении и системе

