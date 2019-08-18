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

app = QApplication(sys.argv)

class WOJTest(unittest.TestCase):
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
        self.scenario['spins'] = [
            "pickBecomeBankrupt",
            "pickBecomeBankrupt",
            "pickBecomeBankrupt",
            "pickRandomCategory1",
            "pickBecomeBankrupt",
            "pickBecomeBankrupt",
            "pickDoublePlayerRoundScore",
        ]
        self.args = build_args(logging.DEBUG, 10000, json.dumps(self.scenario))
        self.game = game.Game(**self.args['game'])
        self.game.start()
        self.hmi = hmi.HMI(**self.args['hmi'])
        self.hmi.show()
        QTest.qWait(2000)

        spinWidget = self.hmi.doSpin

        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)


        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(self.hmi.button_reveal, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(self.hmi.button_correct, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)

        QTest.mouseClick(spinWidget, Qt.LeftButton)
        QTest.qWait(1000)
        self.assertEquals(self.hmi.player0Score.text(), 200)


if __name__ == "__main__":
    unittest.main()