#!/usr/bin/env python3
__author__ = 'Sergey Maksimov'
__mail__ = 'm6v@mail.ru'
__version__ = '0.2'
__date__ = '2025-10-02'
__copyright__ = 'Copyright © 2025 Sergey Maksimov'
__licence__ = 'GNU Public Licence (GPL) v3'

import configparser
import os
import sys
from PyQt5.Qt import QApplication

from MainWindow import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
