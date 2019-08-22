import sys
import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from main import build_args
import hmi
import game
import json
import logging
import logging
import logs
app = QApplication(sys.argv)

global h
h = list()



class WOJTest(unittest.TestCase):
    def __init__(self, *args, loglevel=logging.DEBUG, **kwargs):
        super(WOJTest, self).__init__(*args, **kwargs)
        self.hints = list()
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel

    def setUp(self):
        # help from http://johnnado.com/pyqt-qtest-example/
        # help from https://bitbucket.org/jmcgeheeiv/pyqttestexample/src/default/src/MargaritaMixerTest.py
        scenario = dict()

        scenario['players'] = [
            "player1",
            "player2",
            "player3",
        ]
        scenario['options'] = dict()
        scenario['options']['skipSpinAction'] = True
        scenario['options']['skipUserRegistrationWizard'] = True
        scenario['options']['setStartingPlayer'] = 0
        self.scenario = scenario
        #self.args = build_args(logging.DEBUG, 10000, json.dumps(scenario))

    def test_doublescore(self):
        app = QApplication(sys.argv)

        self.scenario['spins'] = [
            "pickBecomeBankrupt",
            "pickBecomeBankrupt",
            "pickBecomeBankrupt",
            "pickRandomCategory1",
            "pickBecomeBankrupt",
            "pickBecomeBankrupt",
            "pickDoublePlayerRoundScore",
        ]
        self.scenario['players'][0] = "doublescore"
        self.args = build_args(logging.DEBUG, 10000, json.dumps(self.scenario), hints=h)
        h.append(self.args['hmi']['hmi_port'])
        h.append(self.args['game']['game_port'])
        self.logger.debug("hints=%s" % self.hints)
        self.game = None
        self.game = game.Game(**self.args['game'])
        self.game.start()
        self.hmi = None
        self.hmi = hmi.HMI(**self.args['hmi'])
        self.hmi.show()
        QTest.qWait(3000)

        spinWidget = self.hmi.buttonSpin

        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)


        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        while not hasattr(self.hmi, "scene_question"):
            QTest.qWait(50)
        QTest.mouseClick(self.hmi.scene_question.buttonReveal, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(self.hmi.scene_question.buttonCorrect, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)

        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.hmi.main_scorebar.player0.getScore(), str(200))
        self.game.quit()
        self.hmi.close()
        QTest.qWait(1000)
        app.exit()

    def test_bankruptcy(self):
        app = QApplication(sys.argv)
        self.scenario['spins'] = [
            "pickRandomCategory1",
            "pickBecomeBankrupt",
            "pickBecomeBankrupt",
            "pickBecomeBankrupt",
        ]
        self.scenario['players'][0] = "0bankruptcy"
        self.args = build_args(logging.DEBUG, 10000, json.dumps(self.scenario), hints=h)
        h.append(self.args['hmi']['hmi_port'])
        h.append(self.args['game']['game_port'])
        self.logger.debug("hints=%s" % self.hints)
        self.game = None
        self.game = game.Game(**self.args['game'])
        self.game.start()
        self.hmi = None
        self.hmi = hmi.HMI(**self.args['hmi'])
        self.hmi.show()
        QTest.qWait(2000)

        spinWidget = self.hmi.buttonSpin

        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        while not hasattr(self.hmi, "scene_question"):
            QTest.qWait(50)
        QTest.mouseClick(self.hmi.scene_question.buttonReveal, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(self.hmi.scene_question.buttonCorrect, Qt.LeftButton)
        QTest.qWait(1000)

        self.assertEqual(self.hmi.main_scorebar.player0.getScore(), str(100))

        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)

        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)

        self.assertEqual(self.hmi.main_scorebar.player0.getScore(), str(0))
        self.game.quit()
        self.hmi.close()
        QTest.qWait(1000)
        app.exit()

    def test_multipledirectcategories(self):
        app = QApplication(sys.argv)
        self.scenario['spins'] = [
            "pickRandomCategory1",
            "pickRandomCategory2",
            "pickRandomCategory3",
        ]
        self.scenario['players'][0] = "multipledirectcategories"
        self.scenario['options']['skipSpinAction'] = False
        self.args = build_args(logging.DEBUG, 10000, json.dumps(self.scenario), hints=h)
        h.append(self.args['hmi']['hmi_port'])
        h.append(self.args['game']['game_port'])
        self.logger.debug("hints=%s" % self.hints)
        self.game = None
        self.game = game.Game(**self.args['game'])
        self.game.start()
        self.hmi = None
        self.hmi = hmi.HMI(**self.args['hmi'])
        self.hmi.show()
        QTest.qWait(2000)

        spinWidget = self.hmi.buttonSpin

        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(10000)
        QTest.mouseClick(self.hmi.scene_question.buttonReveal, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(self.hmi.scene_question.buttonCorrect, Qt.LeftButton)
        QTest.qWait(1000)

        self.assertEqual(self.hmi.main_scorebar.player0.getScore(), str(100))


        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(10000)
        QTest.mouseClick(self.hmi.scene_question.buttonReveal, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(self.hmi.scene_question.buttonCorrect, Qt.LeftButton)
        QTest.qWait(1000)

        self.assertEqual(self.hmi.main_scorebar.player1.getScore(), str(100))
        self.game.quit()
        self.hmi.close()
        QTest.qWait(1000)
        app.exit()

    def test_0spend_multiple_freeturn(self):
        app = QApplication(sys.argv)
        self.scenario['spins'] = [
            "pickAccumulateFreeTurnToken",
            "pickBecomeBankrupt",
            "pickBecomeBankrupt",
            "pickRandomCategory1",
            "pickDoublePlayerRoundScore",
            "pickBecomeBankrupt",
            "pickBecomeBankrupt",
            "pickAccumulateFreeTurnToken",
            "pickBecomeBankrupt",
            "pickBecomeBankrupt",
            "pickLoseTurn",
            "pickBecomeBankrupt",
            "pickBecomeBankrupt",

        ]
        self.scenario['players'][0] = "spend_multiple_freeturn"
        self.scenario['options']['skipSpinAction'] = True
        self.args = build_args(logging.DEBUG, 10000, json.dumps(self.scenario), hints=h)
        h.append(self.args['hmi']['hmi_port'])
        h.append(self.args['game']['game_port'])
        self.logger.debug("hints=%s" % self.hints)
        self.game = None
        self.game = game.Game(**self.args['game'])
        self.game.start()
        self.hmi = None
        self.hmi = hmi.HMI(**self.args['hmi'])
        self.hmi.show()
        QTest.qWait(2000)

        spinWidget = self.hmi.buttonSpin

        self.assertEqual(self.hmi.main_scorebar.player0.getFreeTurnTokens(), str(0))
        self.logger.debug("==============starting spin 1================")
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(5000)

        self.logger.debug("==============starting spin 2================")
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(3000)
        self.logger.debug("==============starting spin 3================")
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(3000)
        self.assertEqual(self.hmi.main_scorebar.player0.getFreeTurnTokens(), str(1))
        self.assertEqual(self.hmi.main_scorebar.player0.getScore(), str(0))

        self.logger.debug("==============starting spin 4================")
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(4000)
        self.logger.debug("right before thought about issue")
        while not hasattr(self.hmi, "scene_question"):
            QTest.qWait(50)

        self.logger.debug("==============starting spin 5================")
        QTest.mouseClick(self.hmi.scene_question.buttonReveal, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(self.hmi.scene_question.buttonIncorrect, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(self.hmi.scene_question.buttonFreeTurnSpend, Qt.LeftButton)
        QTest.qWait(3000)
        self.assertEqual(self.hmi.main_scorebar.player0.getScore(), "-100")
        self.assertEqual(self.hmi.main_scorebar.player0.getFreeTurnTokens(), str(0))


        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.hmi.main_scorebar.player0.getScore(), "-200")



        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)

        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.hmi.main_scorebar.player0.getFreeTurnTokens(), str(1))
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)

        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        while not hasattr(self.hmi, "scene_question"):
            QTest.qWait(50)
        QTest.mouseClick(self.hmi.scene_question.buttonFreeTurnSpend, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEqual(self.hmi.main_scorebar.player0.getFreeTurnTokens(), str(0))
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)

        self.assertEqual(self.hmi.main_scorebar.player0.getFreeTurnTokens(), str(0))
        self.game.quit()
        self.hmi.close()
        QTest.qWait(1000)
        app.exit()

if __name__ == "__main__":
    unittest.main()