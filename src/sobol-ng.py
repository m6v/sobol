#!/usr/bin/env python3
import argparse
import json
import logging
import sys
from pathlib import Path

# Модуль для вывода сообщений о системных segfaults
import faulthandler
faulthandler.enable()

from PySide2 import QtWidgets

from MainWindow import MainWindow

from config import config

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    parser = argparse.ArgumentParser(description='Эмулятор ПАК "Соболь"')
    parser.add_argument("config", nargs="?", help="Конфигурационный файл")
    args = parser.parse_args()

    # Если конфиг не задан, используем $HOME/.config/$program_name/default.conf
    program_name = Path(sys.argv[0]).stem
    if not args.config:
        config_path = Path.home().joinpath(".config", program_name, "default.conf")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.touch()
        logging.warning(f"Configuration file not specified, using '{config_path}'")
    else:
        config_path = Path(args.config)
        # Если путь к конфигу не задан (только имя),
        # ищем файл args.config в каталоге $HOME/.config/$program_name
        if len(config_path.parts) == 1:
            config_path = Path.home().joinpath(".config", program_name, args.config)

        if not config_path.exists():
            logging.error(f"Config {config_path} not found")
            sys.exit(1)
    try:
        config.read(config_path)
        # Список из идентификаторов iButton зарегистрированных администраторов
        config.admins = json.loads(config.get("general", "admins", fallback="[]"))
        # Список из словарей с настройками зарегистрированных пользователей
        config.users = json.loads(config.get("general", "users", fallback="[]"))
        # Число неудачных попыток входа
        config.failed_logins = int(config.get("general", "failed_logins", fallback="0"))
        # Имя файла с журналом событий
        config.journal_file = config.get("general", "journal_file", fallback=Path(config_path).with_suffix('.log'))
    except configparser.NoOptionError as e:
        logging.warning(e)
    except configparser.NoSectionError as e:
        logging.error(e)    

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    status = app.exec_()

    config.set("general", "admins", json.dumps(config.admins, ensure_ascii=False))
    config.set("general", "users", json.dumps(config.users, ensure_ascii=False))
    config.set("general", "failed_logins", str(config.failed_logins))

    with open(config_path, "w") as file:
        config.write(file)

    sys.exit(status)
