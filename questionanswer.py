
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QObject, QThread
from PyQt5 import uic, QtWidgets
from PyQt5 import QtCore
import logging
from timeit import default_timer as timer
import logs
from HoverButton import HoverButton
from CategoryLabel import CategoryLabel
from QuestionLabel import QuestionLabel
from ValueLabel import ValueLabel
from ScoreBar import ScoreBar
from PlayerFrame import PlayerFrame

from PyQt5 import QtTest

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

        self.vstackLayout.setStretchFactor(self.contextLayout, 1)
        self.vstackLayout.setStretchFactor(self.headerLayout, 1)
        self.vstackLayout.setStretchFactor(self.bodyLayout, 4)
        self.vstackLayout.setStretchFactor(self.controlLayout, 1)
        self.timer = QtWidgets.QLCDNumber(self)

        self.scorebar = ScoreBar(self)
        self.contextLayout.addWidget(self.scorebar)
        self.contextLayout.addWidget(self.timer)

        self.qvalueLayout = QtWidgets.QVBoxLayout()
        self.qvalueLayout.setObjectName("qvalueLayout")
        self.labelValueUpper = QtWidgets.QLabel(self)
        self.labelValueUpper.setText("For")
        self.labelValueUpper.setAlignment(Qt.AlignCenter)
        self.labelValueLower = QtWidgets.QLabel(self)
        self.labelValueLower.setText("Points")
        self.labelValueLower.setAlignment(Qt.AlignCenter)
        self.labelValueName = ValueLabel(self)
        self.labelValueName.setAlignment(Qt.AlignCenter)
        self.qvalueLayout.addWidget(self.labelValueUpper)
        self.qvalueLayout.addWidget(self.labelValueName)
        self.qvalueLayout.addWidget(self.labelValueLower)
        self.qvalueLayout.setStretchFactor(self.labelValueUpper, 1)
        self.qvalueLayout.setStretchFactor(self.labelValueName,100)
        self.qvalueLayout.setStretchFactor(self.labelValueLower, 1)

        self.contextLayout.addLayout(self.qvalueLayout)
        self.contextLayout.setStretchFactor(self.scorebar, 5)
        self.contextLayout.setStretchFactor(self.timer, 2)
        self.contextLayout.setStretchFactor(self.qvalueLayout, 1)

        self.labelQuestionNameNew = QuestionLabel(self)
        self.labelQuestionNameNew.setAlignment(Qt.AlignCenter)
        self.bodyLayout.replaceWidget(self.labelQuestionName, self.labelQuestionNameNew)
        self.labelQuestionName.hide()

        self.labelCategoryNameNew = CategoryLabel(self)
        self.labelCategoryNameNew.setAlignment(Qt.AlignCenter)
        self.headerLayout.replaceWidget(self.labelCategoryName, self.labelCategoryNameNew)
        self.labelCategoryName.hide()


        self.buttonReveal = HoverButton()
        self.buttonReveal.setText("Reveal Answer")
        self.buttonReveal.setAlignment(Qt.AlignCenter)
        self.buttonReveal.clicked.connect(self.somethingClicked)
        self.buttonReveal.hide()

        self.buttonCorrect = HoverButton(self)
        self.buttonCorrect.setText("Correct")
        self.buttonCorrect.setAlignment(Qt.AlignCenter)
        self.buttonCorrect.clicked.connect(self.action_correct)
        self.buttonCorrect.hide()

        self.buttonIncorrect = HoverButton(self)
        self.buttonIncorrect.setText("Incorrect")
        self.buttonIncorrect.setAlignment(Qt.AlignCenter)
        self.buttonIncorrect.clicked.connect(self.action_incorrect)
        self.buttonIncorrect.hide()

        self.buttonFreeTurnSpend = HoverButton(self)
        self.buttonFreeTurnSpend.setText("Spend FreeTurn Token")
        self.buttonFreeTurnSpend.setAlignment(Qt.AlignCenter)
        self.buttonFreeTurnSpend.clicked.connect(self.action_spendfreeturn)
        self.buttonFreeTurnSpend.hide()

        self.buttonFreeTurnSkip = HoverButton(self)
        self.buttonFreeTurnSkip.setText("Skip")
        self.buttonFreeTurnSkip.setAlignment(Qt.AlignCenter)
        self.buttonFreeTurnSkip.clicked.connect(self.action_skipfreeturn)
        self.buttonFreeTurnSkip.hide()

    def set_context(self, data) -> None:
        self.scorebar.updatePlayers(data)

        self.logger.debug("at set_context")
        self.labelCurrentPlayer.hide()

        self.timer.setGeometry(QtCore.QRect(130, 387, 64, 23))
        self.timer.setObjectName("timer")
        self.timer.setEnabled(True)
        self.timer.setDigitCount(len(str(float("1"))))
        self.timer.display("1")
        self.timer.setDigitCount(2)

    def set_value(self, value: str) -> None:
        self.labelValueName.setText(value)
        self.labelValueName.show()

    def set_question(self, question: str) -> None:
        self.labelQuestionNameNew.setText(question)
        self.labelQuestionNameNew.show()

    def set_category(self, category: str) -> None:
        self.labelCategoryNameNew.setText(category)
        self.labelCategoryNameNew.show()

    def set_answer(self, answer: str) -> None:
        self.labelQuestionNameNew.setText(answer)
        self.labelQuestionNameNew.show()

    def render_controls_reveal(self) -> None:
        for i in reversed(range(self.controlLayout.count())):
            self.controlLayout.itemAt(i).widget().hide()
        self.buttonReveal.show()
        self.controlLayout.addWidget(self.buttonReveal)

    def render_controls_correct_incorrect(self) -> None:
        for i in reversed(range(self.controlLayout.count())):
            self.controlLayout.itemAt(i).widget().hide()
        self.buttonIncorrect.show()
        self.buttonCorrect.show()
        self.controlLayout.addWidget(self.buttonCorrect)
        self.controlLayout.addWidget(self.buttonIncorrect)

        self.controlLayout.setStretchFactor(self.buttonCorrect, 2)
        self.controlLayout.setStretchFactor(self.buttonIncorrect, 2)

    def render_controls_freeturn(self) -> None:
        for i in reversed(range(self.controlLayout.count())):
            self.controlLayout.itemAt(i).widget().hide()
        self.buttonFreeTurnSkip.show()
        self.buttonFreeTurnSpend.show()
        self.controlLayout.addWidget(self.buttonFreeTurnSpend)
        self.controlLayout.addWidget(self.buttonFreeTurnSkip)

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

    @pyqtSlot(str)
    def updateTimer(self, string):
        self.timer.setDigitCount(len(str(float(string))))
        self.timer.display(string)
