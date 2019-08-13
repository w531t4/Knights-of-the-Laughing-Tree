
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
    from ui import Ui_MainWindow
else:
    class Ui_MainWindow:
        pass

class MyWizard(QtWidgets.QWizard, QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, parent = None, ui_file=None, loglevel=logging.INFO):
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
        self.logger.debug("testtest")