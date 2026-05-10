#!/usr/bin/env python3

__author__ = "Sergey Maksimov"
__mail__ = "m6v@mail.ru"
__version__ = '2.3'
__date__ = "2026-05-09"
__copyright__ = "Copyright © 2026 Sergey Maksimov"
__licence__ = "GNU Public Licence (GPL) v3"
__application__ = "sobol4"
__description__ = 'Эмулятор ПАК "Соболь"'

import argparse
import configparser
import json
import logging
import sys
from pathlib import Path

# Модуль для вывода сообщений о segfaults
import faulthandler
faulthandler.enable()

from PySide2 import QtCore, QtWidgets

from config import config
from MainWindow import MainWindow


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument("config", nargs="?", help="Конфигурационный файл")
    args = parser.parse_args()

    # Если конфиг не задан, используем $HOME/.config/$program_name/default.conf
    program_name = Path(sys.argv[0]).stem
    if not args.config:
        config_file = Path.home().joinpath(".config", program_name, "default.conf")
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.touch()
        logging.warning(f"Configuration file not specified, using '{config_file}'")
    else:
        config_file = Path(args.config)
        # Если путь к конфигу не задан (только имя),
        # ищем файл args.config в каталоге $HOME/.config/$program_name
        if len(config_file.parts) == 1:
            config_file = Path.home().joinpath(".config", program_name, args.config)

        if not config_file.exists():
            logging.error(f"Config {config_file} not found")
            sys.exit(1)
    try:
        config.read(config_file)
        # Заголовок окна
        config.window_title = config.get("window", "title", fallback='ПАК "Соболь"')
        # Разбить строку на элементы, преобразовать их в целые числа и получить QRect с геометрией главного окна
        config.window_geometry = QtCore.QRect(*map(int, config.get("window", "geometry", fallback="0;0;1200;800").split(";")))
        # Состояние окна
        config.window_state = int(config.get("window", "state", fallback="0"))
        # Список из идентификаторов iButton зарегистрированных администраторов
        config.admins = json.loads(config.get("general", "admins", fallback="[]"))
        # Список из словарей с настройками зарегистрированных пользователей
        config.users = json.loads(config.get("general", "users", fallback="[]"))
        # Число неудачных попыток входа
        config.failed_logins = int(config.get("general", "failed_logins", fallback="0"))
        # Имя файла с журналом событий
        config.journal_file = config.get("general", "journal_file", fallback=Path(config_file).with_suffix('.log'))
    except configparser.NoOptionError as e:
        logging.warning(e)
    except configparser.NoSectionError as e:
        logging.error(e)

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    status = app.exec_()

    config.set("window", "geometry", ";".join(map(str, config.window_geometry)))
    config.set("window", "state", str(config.window_state))
    config.set("general", "admins", json.dumps(config.admins, ensure_ascii=False))
    config.set("general", "users", json.dumps(config.users, ensure_ascii=False))
    config.set("general", "failed_logins", str(config.failed_logins))

    with open(config_file, "w") as file:
        config.write(file)

    sys.exit(status)
