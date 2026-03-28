#!/usr/bin/env python3
'''
Пример скрипта запускающего virt-viewer и изменяющего его геометрию
'''
import logging
import re
import subprocess
import sys
import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

domain_name = "arm-abi"
subprocess.Popen(["virt-viewer", domain_name])
win_id = None

pattern = re.compile(r"(^\S*).*arm-abi.*Virt Viewer")
ts = datetime.datetime.now()
# Повторять пока не найдено окно запущенной программы и не достигнут таймаут 1 сек

while (not win_id) and (datetime.datetime.now() - ts < datetime.timedelta(seconds=1)):
    process = subprocess.Popen(["wmctrl", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    lines = output.decode().splitlines()
    for line in lines:
        match = pattern.match(line)
        if match:
            win_id = match.group(1)
            break

try:
    if win_id:
        subprocess.Popen(["wmctrl", "-ir", win_id, "-e", "0,200,50,1000,800"])
except FileNotFoundError as e:
    logging.error(e)

sys.exit(0)
