
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5 import uic, QtWidgets

import logging
import logs


# We'll keep this during development as turning this off and ingesting the raw py allows for things like autocomplete
global IMPORT_UI_ONTHEFLY
# If this is set to False, ui.py must be manually updated by issuing pyuic5
IMPORT_UI_ONTHEFLY = True
# END

if not IMPORT_UI_ONTHEFLY:
    from register_user_wizard import Ui_Wizard
else:
    class Ui_Wizard:
        pass


class MyWizard(QtWidgets.QWizard, QtWidgets.QMainWindow, Ui_Wizard):

    signal_submit_players = pyqtSignal(list)
    signal_close = pyqtSignal()

    def __init__(self, parent=None, ui_file=None, loglevel=logging.INFO):
        super(MyWizard, self).__init__(parent)
        if not IMPORT_UI_ONTHEFLY:
            self.setupUi(self)
        else:
            # used for on-the-fly compilation of ui xml
            if ui_file is None:
                raise Exception("Did not specify a .ui file")
            uic.loadUi(ui_file, self)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
        self.buttonAddPlayer.clicked.connect(self.add_user)
        self.pageUserEntry.signal_ask_for_validation.connect(self.submit_players)
        self.buttonClearPlayers.clicked.connect(self.clearPlayers)

    @pyqtSlot()
    def add_user(self):
        proposedPlayerName = self.inputPlayerName.text()
        if proposedPlayerName != "":
            self.labelFeedback.setText("")
            self.listWidget.addItem(proposedPlayerName)
            self.inputPlayerName.setText("")
        else:
            self.labelFeedback.setText("Must specify a player name")

    @pyqtSlot()
    def submit_players(self):
        list_length = self.listWidget.count()
        list_contents = [self.listWidget.item(x).text() for x in range(0, list_length)]
        self.signal_submit_players.emit(list_contents)

    def closeEvent(self, event):
        self.signal_close.emit()
        super(MyWizard, self).closeEvent(event)

    @pyqtSlot(str)
    def setFeedback(self, string):
        self.labelFeedback.setText(string)

    @pyqtSlot()
    def clearPlayers(self):
        self.listWidget.clear()
