from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5 import uic, QtWidgets
import logging
import logs
from HoverButton import HoverButton

# We'll keep this during development as turning this off and ingesting the raw py allows for things like autocomplete
global IMPORT_UI_ONTHEFLY
# If this is set to False, ui.py must be manually updated by issuing pyuic5
IMPORT_UI_ONTHEFLY = True
# END

if not IMPORT_UI_ONTHEFLY:
    from select_category import Ui_Frame
else:
    class Ui_Frame:
        pass


class MyCatSelect(QtWidgets.QFrame, QtWidgets.QMainWindow, Ui_Frame):

    signal_submit_category = pyqtSignal(str)
    signal_close = pyqtSignal()
    signal_shift_scene = pyqtSignal()

    def __init__(self, parent=None, ui_file=None, loglevel=logging.INFO, categories=[], audience="Player"):
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
        self.categories = categories
        num_categories = len(categories)
        self.signal_close.connect(self.close)
        for i in range(0,num_categories):
            setattr(self, "cat%s" % (i), HoverButton(self))
            getattr(self, "cat%s" % (i)).setScaledContents(True)
            getattr(self, "cat%s" % (i)).setAlignment(Qt.AlignCenter)
            getattr(self, "cat%s" % (i)).setWordWrap(True)
            getattr(self, "cat%s" % (i)).setObjectName("cat%s" % (i))
            getattr(self, "cat%s" % (i)).clicked.connect(self.somethingClicked)
            getattr(self, "cat%s" % (i)).clicked.connect(self.shift_scene)
            getattr(self, "cat%s" % (i)).setText(categories[i])
            self.horizontalLayout_3.addWidget(getattr(self, "cat%s" % (i)))
        self.message.setText("%s, please select a category" % (audience))

    @pyqtSlot(str)
    def somethingClicked(self, s):
        self.logger.debug("Captured the selection of category=%s" % (s))
        self.signal_submit_category.emit(s)
        self.signal_close.emit()

    @pyqtSlot()
    def shift_scene(self):
        self.signal_shift_scene.emit()


