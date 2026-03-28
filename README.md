# Имитатор программно-аппаратного комплекса "Соболь" 4.0

## Установка
```
sudo usermod -aG libvirt $USER;
echo "export LIBVIRT_DEFAULT_URI='qemu:///system'" >> ~/.bashrc
source ~/.bashrc
sudo cp ibutton2dbus.desktop /etc/xdg/autostart
```

## Особенности версии с novnc
1. установить пакеты `novnc` и `python3-websockify`
2. в настройках виртуальной машины добавить Display VNC с портом, например, 5901
2. сделать автозапуск
```
websockify 6080 127.0.0.1:5901 --web /usr/share/novnc
python3 -m http.server
```

## Установка зависимостей
Если нет pip, то зависимости из requirements.txt можно установить командой
```
sed -E '/^\s*#/d;s/[=<>].*//' requirements.txt | tr '\n' ' ' | xargs sudo apt install
```

## Видеоруководства
[[https://yandex.ru/video/preview/11134341846140738338]]
[[https://dzen.ru/video/watch/610957f659eaef364db52115]]
