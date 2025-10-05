# sobol
Имитатор программно-аппаратного комплекса "Соболь"

До запуска программы запустить
- ibutton2dbus (эмулятор чтения iButton, передающий идентификатор в сессионную dbus)
- websockify  6080 127.0.0.1:5901 --web /usr/share/novnc

Зависимости:
- python3-pyqt5 (если по дефолту не установлен)
- python3-pyqt5.qtwebengine
- python3-pydbus
- python3-libvirt
- novnc
- python3-websockify (если по дефолту не установлен или не ставится с novnc)

