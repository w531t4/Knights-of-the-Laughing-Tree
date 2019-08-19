from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal
import logs
import logging


# We'll keep this during development as turning this off and ingesting the raw py allows for things like autocomplete
# If this is set to False, ui.py must be manually updated by issuing pyuic5
IMPORT_UI_ONTHEFLY = True
# END

if not IMPORT_UI_ONTHEFLY:
    from playerframe import Ui_PlayerFrame
else:
    class Ui_PlayerFrame:
        pass


class PlayerFrame(QtWidgets.QFrame, Ui_PlayerFrame):

    clicked = pyqtSignal(str)

    #Help from https://stackoverflow.com/questions/9384305/hover-issue-in-pyqt
    def __init__(self, parent=None,
                 loglevel=logging.DEBUG,
                 ui_file=None,
                 gamescore=0,
                 roundscore=0,
                 freeturns=0,
                 name="",
                 active=False):
        super(PlayerFrame, self).__init__(parent)
        if not IMPORT_UI_ONTHEFLY:
            self.setupUi(self)
        else:
            # used for on-the-fly compilation of ui xml
            if ui_file is None:
                raise Exception("Did not specify a .ui file")
            uic.loadUi(ui_file, self)

        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
        self.playerName = name
        self.setName(self.playerName)
        self.setScore(str(gamescore + roundscore))
        self.setFreeTurnTokens(freeturns)
        if active:
            self.setActive()
        else:
            self.setInactive()

    def setActive(self):
        pass

    def setInactive(self):
        pass

    def getName(self):
        return self.playerName

    def setName(self, name, max_length=8):
        if len(name) > max_length:
            name = name[0:max_length] + ".."
        self.label_playername.setText(name)
        self.label_playername.setStyleSheet('''
                                    font-family: Verdana, Geneva, sans-serif;
                                    font-size: 25px;
                                    color: black;
                                    font-weight: 700;
                                    text-decoration: none;
                                    font-style: normal;
                                    font-variant: normal;
                                    text-transform: capitalize;
                                    ''')

    def setScore(self, score: int):
        self.label_gamescore.setText(str(score))

    def setFreeTurnTokens(self, num_tokens: int):
        self.label_freeturns.setText(str(num_tokens))

    def blah(self):
        self.setMouseTracking(True)
        self.setStyleSheet('''
                            font-family: Arial, Helvetica, sans-serif;
                            background-color: rgb(6,12,233);
                            font-size: 45px;
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
        super(PlayerFrame, self).hide()