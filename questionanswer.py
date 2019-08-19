
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
    from scene_question import Ui_QuestionScene
else:
    class Ui_QuestionScene:
        pass


class MyQuestionScene(QtWidgets.QFrame, QtWidgets.QMainWindow, Ui_QuestionScene
                      ):

    signal_submit_players = pyqtSignal(list)
    signal_close = pyqtSignal()
    signal_reveal = pyqtSignal()
    signal_correct = pyqtSignal()
    signal_incorrect = pyqtSignal()
    signal_spendfreeturn = pyqtSignal()
    signal_skipfreeturn = pyqtSignal()
    signal_shift_scene = pyqtSignal()

    def __init__(self, parent=None, ui_file=None, loglevel=logging.INFO):
        super(MyQuestionScene, self).__init__(parent)
        if not IMPORT_UI_ONTHEFLY:
            self.setupUi(self)
        else:
            # used for on-the-fly compilation of ui xml
            if ui_file is None:
                raise Exception("Did not specify a .ui file")
            uic.loadUi(ui_file, self)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel


    def set_question(self, question: str) -> None:
        self.labelQuestionName.setText(question)

    def set_category(self, category: str) -> None:
        self.labelCategoryName.setText(category)

    def set_answer(self, answer: str) -> None:
        self.labelQuestionName.setText(answer)

    def render_controls_reveal(self) -> None:
        self.buttonReveal = HoverButton()
        self.buttonReveal.clicked.connect(self.somethingClicked)
        self.buttonReveal.setText("Reveal Answer")
        self.buttonReveal.setAlignment(Qt.AlignCenter)
        self.controlsLayout.addWidget(self.buttonReveal)

    def render_controls_correct_incorrect(self) -> None:
        #self.buttonReveal.setParent(None)
        #self.buttonReveal.hide()
        for i in reversed(range(self.controlsLayout.count())):
            self.controlsLayout.itemAt(i).widget().hide()

        self.buttonCorrect = HoverButton(self)
        self.buttonCorrect.setText("Correct")
        self.buttonCorrect.setAlignment(Qt.AlignCenter)
        self.buttonCorrect.clicked.connect(self.action_correct)
        self.controlsLayout.addWidget(self.buttonCorrect)

        self.buttonIncorrect = HoverButton(self)
        self.buttonIncorrect.setText("Incorrect")
        self.buttonIncorrect.setAlignment(Qt.AlignCenter)
        self.buttonIncorrect.clicked.connect(self.action_incorrect)
        self.controlsLayout.addWidget(self.buttonIncorrect)

    def render_controls_freeturn(self) -> None:
        # self.buttonReveal.setParent(None)
        # self.buttonReveal.hide()
        for i in reversed(range(self.controlsLayout.count())):
            self.controlsLayout.itemAt(i).widget().hide()

        self.buttonFreeTurnSpend = HoverButton(self)
        self.buttonFreeTurnSpend.setText("Spend FreeTurn Token")
        self.buttonFreeTurnSpend.setAlignment(Qt.AlignCenter)
        self.buttonFreeTurnSpend.clicked.connect(self.action_spendfreeturn)
        self.controlsLayout.addWidget(self.buttonFreeTurnSpend)

        self.buttonFreeTurnSkip = HoverButton(self)
        self.buttonFreeTurnSkip.setText("Skip")
        self.buttonFreeTurnSkip.setAlignment(Qt.AlignCenter)
        self.buttonFreeTurnSkip.clicked.connect(self.action_skipfreeturn)
        self.controlsLayout.addWidget(self.buttonFreeTurnSkip)

    @pyqtSlot(str)
    def action_reveal(self, s: str) -> None:
        self.logger.debug("received action (reveal) [%s]" % s)
        self.signal_reveal.emit()

    @pyqtSlot(str)
    def action_correct(self, s: str) -> None:
        self.logger.debug("received action (correct) [%s]" % s)
        self.signal_correct.emit()

    @pyqtSlot(str)
    def action_incorrect(self, s: str) -> None:
        self.logger.debug("received action (incorrect) [%s]" % s)
        self.signal_incorrect.emit()

    @pyqtSlot(str)
    def action_spendfreeturn(self, s: str) -> None:
        self.logger.debug("received action (spendfreeturn) [%s]" % s)
        self.signal_spendfreeturn.emit()

    @pyqtSlot(str)
    def action_skipfreeturn(self, s: str) -> None:
        self.logger.debug("received action (skipfreeturn) [%s]" % s)
        self.signal_skipfreeturn.emit()

    @pyqtSlot(str)
    def somethingClicked(self, s):
        self.logger.debug("Captured the selection of %s" % (s))
        self.signal_reveal.emit()

