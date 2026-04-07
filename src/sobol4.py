#!/usr/bin/env python3
__author__ = "Sergey Maksimov"
__mail__ = "m6v@mail.ru"
__version__ = '1.3'
__date__ = "2026-03-24"
__copyright__ = "Copyright © 2026 Sergey Maksimov"
__licence__ = "GNU Public Licence (GPL) v3"
__application__ = "sobol4"

import argparse
import configparser
import libvirt
import logging
import os
import subprocess
import sys
from pathlib import Path
from PySide2.QtWidgets import QApplication

from constants import VIR_DOMAIN_STATE_MAPPING
from MainWindow import MainWindow

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


def main():
    app = QApplication(sys.argv)
    window = MainWindow(path)
    sys.exit(app.exec_())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Эмулятор ПАК "Соболь"')
    parser.add_argument("config", nargs="?", help="Конфигурационный файл")
    args = parser.parse_args()

    # Если конфиг не задан, используем $HOME/.config/sobol4/default.conf
    if not args.config:
        path = Path.home() / ".config" / __application__ / "default.conf"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        logging.warning(f"No config file specified, using {path}")
    else:
        path = Path(args.config)
        # Если путь к конфигу не задан, ищем в $HOME/.config/sobol4
        if len(path.parts) == 1:
            path = Path.home() / ".config" / __application__ / args.config

        if not path.exists():
                logging.error(f"Config {path} not found")
                sys.exit(1)

    config = configparser.ConfigParser(allow_no_value=True)
    # Установить чувствительность ключей к регистру
    config.optionxform = str
    config.read(path)
    domain_name = config.get("general", "domain_name", fallback="")

    try:
        # Регистрация стандартной реализации цикла событий
        libvirt.virEventRegisterDefaultImpl()
        # Открыть соединение с локальным гипервизором
        conn = libvirt.open(None)
        dom = conn.lookupByName(domain_name)
        # state - состояние виртуальной машины (число из перечисления virDomainState)
        # reason - причина перехода в определённое состояние (число из перечисления virDomain*Reason)
        state, reason = dom.state()
        logging.info(f"Domain {dom.name()}, state: {VIR_DOMAIN_STATE_MAPPING.get(state)}, reason: {reason}")
        # Если виртуальная машина domain_name не запущена, запустить имитатор ПАК "Соболь", иначе запустить virt-manager
        if state != libvirt.VIR_DOMAIN_RUNNING:
            main()
        else:
            sys.exit(subprocess.Popen(["virt-manager", "--connect", "qemu:///system", "--show-domain-console", domain_name]))
    except libvirt.libvirtError as e:
        # Исключение выбрасывается, если среда виртуализации не установлена, в этом случае все равно запускаем программу
        logging.debug(e)
        main()
