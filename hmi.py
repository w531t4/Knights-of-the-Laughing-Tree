#!/bin/env python3

import socket
import commsettings
import time
import messaging
import queue
import json
import random
import logging
import logs
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QObject
from PyQt5 import QtWidgets, uic

# We'll keep this during development as turning this off and ingesting the raw py allows for things like autocomplete
global IMPORT_UI_ONTHEFLY
IMPORT_UI_ONTHEFLY = True
# END

if not IMPORT_UI_ONTHEFLY:
    from ui import Ui_MainWindow
else:
    class Ui_MainWindow:
        pass

class HMIMessageController(QThread):
    signal_recieve_message = pyqtSignal(str)

    def __init__(self, loglevel=logging.INFO):
        QThread.__init__(self)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel

        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientqueue = queue.Queue()
        self.msg_controller = messaging.Messaging(commsettings.MESSAGE_BREAKER, self.receiver, self.clientqueue,
                                                                                loglevel=self.loglevel, name="HMILogic")

    def run(self):
        # Configure Socket to allow reuse of sessions in TIME_WAIT. Otherwise, "Address already in use" is encountered
        # Per suggestion on https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use/29217540
        # by ForceBru
        self.receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receiver.bind(("127.0.0.1", commsettings.HMI_LISTEN))
        self.receiver.listen(2)
        self.logger.info("successfully opened port " + str(commsettings.HMI_LISTEN))
        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                self.sender = socket.create_connection(("127.0.0.1", commsettings.GAME_HMI_LISTEN))
                break
            except Exception as e:
                self.logger.error(e)
                time.sleep(1)
                continue

        self.msg_controller.start()

        while True:
            if not self.clientqueue.empty():
                self.signal_recieve_message.emit(self.clientqueue.get())
            time.sleep(.1)

    @pyqtSlot(str)
    def send_message(self, msg):
        self.msg_controller.send_string(self.sender, msg)


class HMILogicController(QObject):

    signal_send_message = pyqtSignal(str)
    signal_update_game_stats = pyqtSignal(dict)
    signal_spin_wheel = pyqtSignal(int)

    def __init__(self, loglevel=logging.INFO):
        QObject.__init__(self)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel

    @pyqtSlot(str)
    def processMessage(self, incoming_message):
        try:
            message = json.loads(incoming_message)
        except json.JSONDecodeError:
            print("HMI: Failed to decode Message")

        # Check for Sane Message
        if not isinstance(message, dict):
            raise Exception("JSON Blob didn't resolve to a dictionary")
        if "action" not in message.keys():
            raise Exception("Message does not possess action key")
        if "arguments" not in message.keys():
            raise Exception("Message does not possess arguments key")

        # Proceed with performing actioning a message
        if message['action'] == "promptCategorySelectByUser":
            response = dict()
            response['action'] = "responseCategorySelect"
            response['arguments'] = self.selectCategory(message['arguments'])
            self.signal_send_message.emit(json.dumps(response))
        elif message['action'] == "promptIncorrectCorrectResponse":
            response = dict()
            response['action'] = "responseQuestion"
            response['arguments'] = self.selectOutcome()
            self.signal_send_message.emit(json.dumps(response))
        elif message['action'] == "displayQuestion":
            response = dict()
            self.displayQuestion(message['arguments'])
            response['action'] = "displayQuestion"
            response['arguments'] = "ACK"
            self.signal_send_message.emit(json.dumps(response))
        elif message['action'] == "promptPlayerRegistration":
            response = dict()
            response['action'] = "responsePlayerRegistration"
            response['arguments'] = self.registerPlayer()
            self.signal_send_message.emit(json.dumps(response))
        elif message['action'] == "spinWheel":
            self.signal_spin_wheel.emit(message['arguments'])
            response = dict()
            response['action'] = message['action']
            response['arguments'] = "ACK"
            self.signal_send_message.emit(json.dumps(response))
        elif message['action'] == "displayWinner":
            self.displayWinner(message['arguments'])
        elif message['action'] == "updateGameState":
            self.signal_update_game_stats.emit(message['arguments'])
            response = dict()
            response['action'] = message['action']
            response['arguments'] = "ACK"
            self.signal_send_message.emit(json.dumps(response))
        else:
            response = dict()
            response['action'] = message['action']
            response['arguments'] = "ACK"
            self.signal_send_message.emit(json.dumps(response))

    @pyqtSlot()
    def askToSpin(self):
        response = dict()
        response['action'] = "userInitiatedSpin"
        response['arguments'] = None
        self.signal_send_message.emit(json.dumps(response))

    def registerPlayer(self):
        """Ask Player what their name is"""
        # TODO: Prompt Players for their Names at the start of a game
        test_names = ["Aaron", "James", "Glenn", "Lorraine", "Markham"]
        r = random.randrange(0, len(test_names))
        return test_names[r]


class HMI(QtWidgets.QMainWindow, Ui_MainWindow):

    signal_send_message = pyqtSignal(str)

    def __init__(self, ui_file=None, loglevel=logging.INFO):
        QtWidgets.QMainWindow.__init__(self)
        if not IMPORT_UI_ONTHEFLY:
            self.setupUi(self)
        else:
            # used for on-the-fly compilation of ui xml
            if ui_file is None:
                raise Exception("Did not specify a .ui file")
            uic.loadUi(ui_file, self)

        self.logger = logs.build_logger(__name__, loglevel)
        #self.textBrowser.setText("blahblah")
        self.loglevel=loglevel

        self.MSG_controller = HMIMessageController(loglevel=loglevel)

        self.logic_controller = HMILogicController(loglevel=loglevel)
        self.logic_controller_thread = QThread(self)

        # Pass messages received to the logic controller
        self.MSG_controller.signal_recieve_message.connect(self.logic_controller.processMessage)

        # Pass responses from the logic controller into the output of the message conroller
        self.logic_controller.signal_send_message.connect(self.MSG_controller.send_message)

        # Pass requests from the logic controller to update game stats to the HMI engine
        self.logic_controller.signal_update_game_stats.connect(self.updateStats)

        # Pass requests from the logic controller to spin the wheel to the HMI engine
        self.logic_controller.signal_spin_wheel.connect(self.spinWheel)

        self.logic_controller.moveToThread(self.logic_controller_thread)

        self.logic_controller_thread.start()
        self.MSG_controller.start()

        self.doSpin.clicked.connect(self.logic_controller.askToSpin)

    def issuePrompt(self):
        pass
    def selectCategory(self, categories):
        """Prompt user or opponents to select a category"""
        if isinstance(categories, list):
            if len(categories) <= 0:
                raise Exception("Category List does not include a sane value")
            else:
                # TODO: Implement UI for selecting from list of categories
                return categories[random.randrange(0, len(categories))]
    def selectOutcome(self):
        """Prompt players to indicate whether a reponse was correct or incorrect"""
        response = random.randrange(0,2)
        if (response == 1):
            return "Correct"
        else:
            return "Incorrect"

    def displayQuestion(self, question):
        """Render provided question to display"""


    def spinWheel(self, destination):
        """ Make the Wheel Spin. Ensure it lands on Destination"""
        self.spinOutcomeLCD.display(destination)
        pass

    @pyqtSlot(dict)
    def updateStats(self, data):
        # Update Player Data
        if "players" not in data.keys():
            raise Exception("Missing player information in update data")
        if len(data['players']) == 0:
            raise Exception("Player entry in update data is empty")
        for person in data['players']:
            self.updatePlayer(person)

        # Update Spins, etc
        self.numSpins.setText(str(data['spinsExecuted']) + "/" + str(data['maxSpins']))
        self.roundNumber.setText(str(data['round']) + "/" + str(data['totalRounds']))

    def updatePlayer(self, playerargs):
        getattr(self, "player" + str(playerargs['id']) + "Name").setText(playerargs['name'])
        getattr(self, "player" + str(playerargs['id']) + "Score").setText(str(playerargs['gameScore']
                                                                          + playerargs['roundScore']))
        getattr(self, "player" + str(playerargs['id']) + "FT").setText(str(playerargs['freeTurnTokens']))

    def displayWinner(self, playername):
        self.labelWinner.setEnabled(True)
        self.winnerName.setText(playername)