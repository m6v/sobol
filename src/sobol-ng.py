#!/usr/bin/env python3
import argparse
import configparser
import logging
import sys
from pathlib import Path

import faulthandler
faulthandler.enable()

from PySide2 import QtWidgets

from MainWindow import MainWindow


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

    config = configparser.ConfigParser(allow_no_value=True)
    # Установить чувствительность ключей к регистру
    config.optionxform = str
    config.read(config_path)

    # Считываем имя файла с журналом событий здесь, для того, чтобы при отсутствии параметра
    # использовать имя файла конфигурации с расширением log
    config.journal_file = config.get("general", "journal_file", fallback=Path(config_path).with_suffix('.log'))

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(config)
    window.show()
    status = app.exec_()

    with open(config_path, "w") as file:
        config.write(file)

    sys.exit(status)
