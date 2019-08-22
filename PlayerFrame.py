from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal, Qt
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
        self.active = False
        self.playerName = name
        self.setName(self.playerName)
        self.setScore(str(gamescore + roundscore))
        self.setFreeTurnTokens(freeturns)
        if active:
            self.setActive()
        else:
            self.setInactive()

    def setActive(self):
        self.active = True
        self.setName(self.playerName)

    def setInactive(self):
        self.active = False
        self.setName(self.playerName)

    def getName(self):
        return self.playerName

    def setName(self, name, max_length=8):
        if len(name) > max_length:
            name = name[0:max_length] + ".."
        self.label_playername.setText(name)
        if self.active:
            self.label_playername.setStyleSheet('''
                                                font-family: Verdana, Geneva, sans-serif;
                                                font-size: 50px;
                                                color: white;
                                                font-weight: 700;
                                                text-decoration: none;
                                                font-style: normal;
                                                font-variant: normal;
                                                text-transform: capitalize;
                                                ''')
        else:

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
        self.label_gamescore.setAlignment(Qt.AlignLeft)
        self.label_gamescore.setStyleSheet('''
                                    font-family: Verdana, Geneva, sans-serif;
                                    font-size: 75px;
                                    color: black;
                                    font-weight: 700;
                                    text-decoration: none;
                                    font-style: normal;
                                    font-variant: normal;
                                    text-transform: capitalize;
                                    ''')

    def setFreeTurnTokens(self, num_tokens: int):
        self.label_freeturns.setText(str(num_tokens))

    def mousePressEvent(self, event):
        self.logger.debug("mousepressevent occurred, i am %s" % (self.objectName()))
        if hasattr(self, "text"):
            self.clicked.emit(self.text())
            QtWidgets.QLabel.mousePressEvent(self, event)

    def hide(self) -> None:
        self.logger.debug("actioning hide")
        super(PlayerFrame, self).hide()