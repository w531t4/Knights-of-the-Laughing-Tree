#!/bin/env python3


import logging
import logs
from PyQt5.QtCore import QThread, pyqtSignal


class Board(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self, loglevel=logging.INFO):
        QThread.__init__(self)
        self.logger = logs.build_logger(__name__, loglevel)


    def flipQuestion(self, category):
        # Flip over the correct category card
        pass
