from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import QLabel
import logs
import logging
from PlayerFrame import PlayerFrame

# We'll keep this during development as turning this off and ingesting the raw py allows for things like autocomplete
global IMPORT_UI_ONTHEFLY
# If this is set to False, ui.py must be manually updated by issuing pyuic5
IMPORT_UI_ONTHEFLY = True
# END

if not IMPORT_UI_ONTHEFLY:
    from rsframe import Ui_RSFrame
else:
    class Ui_RSFrame:
        pass


class RoundSpinFrame(QtWidgets.QFrame, QtWidgets.QMainWindow, Ui_RSFrame):

    def __init__(self,
                 parent=None,
                 ui_file="rsframe.ui",
                 loglevel=logging.DEBUG
                 ):

        super(RoundSpinFrame, self).__init__(parent)
        if not IMPORT_UI_ONTHEFLY:
            self.setupUi(self)
        else:
            # used for on-the-fly compilation of ui xml
            if ui_file is None:
                raise Exception("Did not specify a .ui file")
            uic.loadUi(ui_file, self)

        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
        self.labelRoundCaption = QLabel(self)
        self.labelRoundNumber = QLabel(self)
        self.labelRoundTotal = QLabel(self)
        self.labelSpinsCaption = QLabel(self)
        self.labelSpinsOccurred = QLabel(self)
        self.labelSpinsMax = QLabel(self)

        self.roundValueLayout = QtWidgets.QVBoxLayout(self)
        self.spinsValueLayout = QtWidgets.QVBoxLayout(self)


        self.baseLayout.setObjectName("baseLayout")
        self.roundLayout.addWidget(self.labelRoundCaption)
        self.roundLayout.addLayout(self.roundValueLayout)
        self.roundLayout.setStretchFactor(self.labelRoundCaption, 5)
        self.roundLayout.setStretchFactor(self.roundValueLayout, 5)

        self.roundValueLayout.addWidget(self.labelRoundNumber)
        self.roundValueLayout.addWidget(self.labelRoundTotal)
        self.roundValueLayout.setStretchFactor(self.labelRoundNumber, 2)
        self.roundValueLayout.setStretchFactor(self.labelRoundTotal, 1)


        self.spinsLayout.addWidget(self.labelSpinsCaption)
        self.spinsLayout.addLayout(self.spinsValueLayout)
        self.spinsLayout.setStretchFactor(self.labelSpinsCaption, 5)
        self.spinsLayout.setStretchFactor(self.spinsValueLayout, 5)

        self.spinsValueLayout.addWidget(self.labelSpinsOccurred)
        self.spinsValueLayout.addWidget(self.labelSpinsMax)
        self.spinsValueLayout.setStretchFactor(self.labelSpinsOccurred, 2)
        self.spinsValueLayout.setStretchFactor(self.labelSpinsMax, 1)

        self.setRound()
        self.setRoundTotal()
        self.setSpinsMax()
        self.setSpinsOccurred()

        self.show()

    @pyqtSlot(float)
    def setMaxHeight(self, height):
        self.setMaximumHeight(height)

    def setRound(self, roundNumber: int = 0) -> None:
        self.labelRoundCaption.setText("Round")
        self.labelRoundCaption.setStyleSheet('''
                                    font-family: Verdana, Geneva, sans-serif;
                                    font-size: 15px;
                                    color: black;
                                    font-weight: 700;
                                    text-decoration: none;
                                    font-style: normal;
                                    font-variant: normal;
                                    text-transform: capitalize;
                                    ''')
        self.labelRoundNumber.setText(str(roundNumber))
        self.labelRoundNumber.setAlignment(Qt.AlignCenter)
        self.labelRoundNumber.setStyleSheet('''
                                    font-family: Verdana, Geneva, sans-serif;
                                    font-size: 15px;
                                    color: black;
                                    font-weight: 700;
                                    text-decoration: none;
                                    font-style: normal;
                                    font-variant: normal;
                                    text-transform: capitalize;
                                    ''')

    def setRoundTotal(self, maxRounds: int = 2) -> None:
        self.labelRoundTotal.setText("of %s" % str(maxRounds))
        self.labelRoundTotal.setAlignment(Qt.AlignCenter)
        self.labelRoundTotal.setStyleSheet('''
                                    font-family: Verdana, Geneva, sans-serif;
                                    font-size: 15px;
                                    color: black;
                                    font-weight: 700;
                                    text-decoration: none;
                                    font-style: normal;
                                    font-variant: normal;
                                    text-transform: capitalize;
                                    ''')


    def setSpinsMax(self, max: int = 50) -> None:
        self.labelSpinsMax.setText("of %s" % str(max))
        self.labelSpinsMax.setAlignment(Qt.AlignCenter)
        self.labelSpinsMax.setStyleSheet('''
                                    font-family: Verdana, Geneva, sans-serif;
                                    font-size: 15px;
                                    color: black;
                                    font-weight: 700;
                                    text-decoration: none;
                                    font-style: normal;
                                    font-variant: normal;
                                    text-transform: capitalize;
                                    ''')

    def setSpinsOccurred(self, spinsOccurred: int = 0) -> None:
        stylesheet = '''
                                    font-family: Verdana, Geneva, sans-serif;
                                    font-size: 15px;
                                    color: black;
                                    font-weight: 700;
                                    text-decoration: none;
                                    font-style: normal;
                                    font-variant: normal;
                                    text-transform: capitalize;
                                    '''
        self.labelSpinsCaption.setText("Spins")
        self.labelSpinsCaption.setAlignment(Qt.AlignCenter)
        self.labelSpinsCaption.setStyleSheet(stylesheet)
        self.labelSpinsOccurred.setText(str(spinsOccurred))
        self.labelSpinsOccurred.setAlignment(Qt.AlignCenter)
        self.labelSpinsOccurred.setStyleSheet(stylesheet)