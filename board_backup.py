#!/bin/env python3


import logging
import logs
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5 import QtWidgets



class Board(QtWidgets.QWidget):

    def __init__(self, parent=None, loglevel=logging.INFO):
        super(Board, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel


class Tile(QtWidgets.QLabel):

    def __init__(self, parent=None, loglevel=logging.INFO):
        super(Tile, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel

        self.setStyleSheet('''
                            background-color: blue;
                            font-family: "Lucida Console", Monaco, monospace;
                            font-size: 22px;
                            color: white;
                            font-weight: 400;
                            text-decoration: none;
                            font-style: normal;
                            font-variant: normal;
                            text-transform: none;
                            ''')

    def setText(self, string) -> None:

        super(Tile, self).setText(string)

class QuestionTile(Tile):

    def __init__(self, parent=None, loglevel=logging.INFO):
        super(QuestionTile, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel


class CategoryTile(Tile):

    def __init__(self, parent=None, loglevel=logging.INFO):
        super(CategoryTile, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel

