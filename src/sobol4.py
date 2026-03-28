#!/usr/bin/env python3
__author__ = "Sergey Maksimov"
__mail__ = "m6v@mail.ru"
__version__ = '1.3'
__date__ = "2026-03-24"
__copyright__ = "Copyright © 2026 Sergey Maksimov"
__licence__ = "GNU Public Licence (GPL) v3"

import argparse
import configparser
import libvirt
import logging
import os
import subprocess
import sys
from PySide2.QtWidgets import QApplication

from constants import VIR_DOMAIN_STATE_MAPPING
from MainWindow import MainWindow

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


def main():
    app = QApplication(sys.argv)
    window = MainWindow(args.config_file)
    sys.exit(app.exec_())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Тренажер администратора безопасности")
    parser.add_argument("config_file", help="Конфигурационный файл")
    args = parser.parse_args()

    config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), args.config_file)
    if not os.path.isfile(config_file):
        logging.error(f"Config {config_file} not found")
        sys.exit(1)

    config = configparser.ConfigParser(allow_no_value=True)
    # Установить чувствительность ключей к регистру
    config.optionxform = str
    config.read(config_file)
    domain_name = config.get("general", "domain_name")

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
