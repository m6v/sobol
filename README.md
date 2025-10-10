# Автоматизированное рабочее место обучаемого администратора безопасности НС КК

Для скачивания novnc
раскомментировать в /etc/apt/sources.lst интернет репозитории Astra Linux
mkdir -p /tmp/novnc
apt install -d -o=dir::cache=/tmp/novnc novnc
установить скачанные пакеты
закомментировать в /etc/apt/sources.lst интернет репозитории Astra Linux

Скопировать ibutton2dbus.desktop в /etc/xdg/autostart

До запуска программы запустить
- ibutton2dbus (эмулятор чтения iButton, передающий идентификатор в сессионную dbus)
- websockify  6080 127.0.0.1:5901 --web /usr/share/novnc
NB! Не забыть в настройках ВМ добавить Display VNC с портом 5901
- python3 -m http.server

##
Зависимости:
- python3-pyqt5 (если по дефолту не установлен)
- python3-pyqt5.qtwebengine
- python3-pydbus
- python3-libvirt
- novnc
- python3-websockify (если по дефолту не установлен или не ставится с novnc)

## Установка необходимых пакетов
apt install python3-pip python3-venv
## Создаем виртуальное окружение
python3 -m venv venv_name
NB! Если будут ошибки, возможно требуется установка пакета python3-venv
## Активируем виртуальное окружение
source venv_name/bin/activate

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

Версия для PySide2
$ pip list
Package        Version 
-------------- --------
libvirt-python 11.8.0  
pip            20.0.2  
pkg-resources  0.0.0   
pycairo        1.26.1  
pydbus         0.6.0   
pygobject      3.48.2  
PySide2        5.15.2.1
setuptools     44.0.0  
shiboken2      5.15.2.1

NB! Из перечисленных пакетов вручную ставились libvirt-python, pydbus, pygobject, PySide2, остальные подтянулись как зависимости



# Установка в Astra Linux 1.7.4
sudo -i
apt install python3-pyside2.qtuitools python3-pyside2.qtwebengine python3-pyside2.qtwebenginewidgets
