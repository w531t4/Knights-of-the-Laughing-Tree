from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
import logs
import logging


class QuestionLabel(QtWidgets.QLabel):

    clicked = pyqtSignal(str)

    #Help from https://stackoverflow.com/questions/9384305/hover-issue-in-pyqt
    def __init__(self, parent=None, loglevel=logging.DEBUG):
        super(QuestionLabel, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
        self.setMouseTracking(True)
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
        self.setWordWrap(True)


    def mousePressEvent(self, event):
        self.logger.debug("mousepressevent occurred, i am %s" % (self.objectName()))
        self.clicked.emit(self.text())
        QtWidgets.QLabel.mousePressEvent(self, event)

    def hide(self) -> None:
        self.logger.debug("actioning hide")
        super(QuestionLabel, self).hide()