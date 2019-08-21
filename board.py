#!/bin/env python3


import logging
import logs

from PyQt5.QtWidgets import QFrame, QLabel, QWidget, QGridLayout
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QRect


class Board(QWidget):

    def __init__(self, parent=None, loglevel=logging.INFO):
        super(Board, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel

        self.setGeometry(QRect(420, 60, 641, 231))
        self.boardLayout = QGridLayout(self)
        self.boardLayout.setContentsMargins(0, 0, 0, 0)

        for colnum in range(1, 7):
            for rownum in range(1, 7):
                setattr(self, "label_board_col%s_row%s" % (colnum, rownum), QLabel())

                getattr(self, "label_board_col%s_row%s" % (colnum, rownum)).setText("")
                getattr(self, "label_board_col%s_row%s" % (colnum, rownum)).setAlignment(Qt.AlignCenter)
                getattr(self, "label_board_col%s_row%s" % (colnum, rownum)).setObjectName("label_board_col%s_row%s" %
                                                                                          (colnum, rownum))
                if rownum == 1:
                    stylesheet = '''
                                background-color:rgb(6,12,233);
                                font-weight: bold;
                                '''
                else:
                    stylesheet = '''
                                background-color:rgb(6,12,233);
                                '''
                getattr(self, "label_board_col%s_row%s" % (colnum, rownum)).setStyleSheet(stylesheet)
                self.boardLayout.addWidget(getattr(self, "label_board_col%s_row%s" % (colnum, rownum)),
                                           rownum-1, colnum - 1, 1, 1)
