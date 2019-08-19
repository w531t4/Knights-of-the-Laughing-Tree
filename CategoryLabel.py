from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
import logs
import logging


class CategoryLabel(QtWidgets.QLabel):

    clicked = pyqtSignal(str)

    #Help from https://stackoverflow.com/questions/9384305/hover-issue-in-pyqt
    def __init__(self, parent=None, loglevel=logging.DEBUG):
        super(CategoryLabel, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
        self.setMouseTracking(True)
        self.setStyleSheet('''
                            font-family: Arial, Helvetica, sans-serif;
                            background-color: rgb(6,12,233);
                            font-size: 45px;
                            letter-spacing: 2px;
                            word-spacing: 2px;
                            color: #FFFFFF;
                            font-weight: 700;
                            text-decoration: none;
                            font-style: normal;
                            font-variant: normal;
                            text-transform: uppercase;
                            ''')

    # Help from https://stackoverflow.com/questions/9384305/hover-issue-in-pyqt
    # def enterEvent(self, event):
    #     self.logger.debug("enter")
    #     self.setStyleSheet('''
    #                         background-color: #1C6EA4;
    #                         font-family: "Lucida Console", Monaco, monospace;
    #                         font-size: 22px;
    #                         color: white;
    #                         font-weight: 400;
    #                         text-decoration: none;
    #                         font-style: normal;
    #                         font-variant: normal;
    #                         text-transform: none;
    #                         ''')

    # Help from https://stackoverflow.com/questions/9384305/hover-issue-in-pyqt
    # def leaveEvent(self, event):
    #     self.setStyleSheet('''
    #                         background-color: blue;
    #                         font-family: "Lucida Console", Monaco, monospace;
    #                         font-size: 22px;
    #                         color: white;
    #                         font-weight: 400;
    #                         text-decoration: none;
    #                         font-style: normal;
    #                         font-variant: normal;
    #                         text-transform: none;
    #                         ''')
    #     self.logger.debug("leave")

    def mousePressEvent(self, event):
        self.logger.debug("mousepressevent occurred, i am %s" % (self.objectName()))
        self.clicked.emit(self.text())
        QtWidgets.QLabel.mousePressEvent(self, event)

    def hide(self) -> None:
        self.logger.debug("actioning hide")
        super(CategoryLabel, self).hide()