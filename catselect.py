
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5 import uic, QtWidgets

import logging
import logs


# We'll keep this during development as turning this off and ingesting the raw py allows for things like autocomplete
global IMPORT_UI_ONTHEFLY
# If this is set to False, ui.py must be manually updated by issuing pyuic5
IMPORT_UI_ONTHEFLY = False
# END

if not IMPORT_UI_ONTHEFLY:
    from select_category import Ui_Frame
else:
    class Ui_Frame:
        pass


class MyCatSelect(QtWidgets.QFrame, QtWidgets.QMainWindow, Ui_Frame):

    signal_submit_players = pyqtSignal(list)

    def __init__(self, parent=None, ui_file=None, loglevel=logging.INFO):
        super(MyCatSelect, self).__init__(parent)
        if not IMPORT_UI_ONTHEFLY:
            self.setupUi(self)
        else:
            # used for on-the-fly compilation of ui xml
            if ui_file is None:
                raise Exception("Did not specify a .ui file")
            uic.loadUi(ui_file, self)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
        self.logger.debug("finish init")

    @pyqtSlot(list)
    def updateCategories(self, catList):
        for categoryAttributes in catList:
            name = categoryAttributes['name']
            selectable = categoryAttributes['isSelectable']

