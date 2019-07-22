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
from PyQt5 import QtWidgets, uic, QtGui

# We'll keep this during development as turning this off and ingesting the raw py allows for things like autocomplete
global IMPORT_UI_ONTHEFLY
IMPORT_UI_ONTHEFLY = False
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
    signal_update_game_stats = pyqtSignal(str, str, str, str)
    signal_update_player_data = pyqtSignal(str, str, str, str, str)
    signal_spin_wheel = pyqtSignal(int)
    signal_select_category = pyqtSignal(list)
    signal_display_winner = pyqtSignal(str)

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

        perform_ack_at_end = True
        # Proceed with performing actioning a message
        if message['action'] == "promptCategorySelectByUser":
            perform_ack_at_end = False
            self.signal_select_category.emit(message['arguments'])
        elif message['action'] == "promptIncorrectCorrectResponse":
            # TODO: Needs conversion to UI model
            perform_ack_at_end = False
            response = dict()
            response['action'] = "responseQuestion"
            response['arguments'] = self.selectOutcome()
            self.signal_send_message.emit(json.dumps(response))
        elif message['action'] == "displayQuestion":
            self.displayQuestion(message['arguments'])
        elif message['action'] == "promptPlayerRegistration":
            # TODO: Needs conversion to UI model
            perform_ack_at_end = False
            response = dict()
            response['action'] = "responsePlayerRegistration"
            response['arguments'] = self.registerPlayer()
            self.signal_send_message.emit(json.dumps(response))
        elif message['action'] == "spinWheel":
            self.signal_spin_wheel.emit(message['arguments'])
        elif message['action'] == "displayWinner":
            self.signal_display_winner.emit(message['arguments'])
        elif message['action'] == "updateGameState":
            # Update Player Data
            if "players" not in message['arguments'].keys():
                raise Exception("Missing player information in update data")
            if len(message['arguments']['players']) == 0:
                raise Exception("Player entry in update data is empty")

            for person in message['arguments']['players']:
                self.signal_update_player_data.emit(str(person['id']),
                                                    str(person['name']),
                                                    str((person['gameScore'] + person['roundScore'])),
                                                    str(person['freeTurnTokens']),
                                                    str(message['arguments']['currentPlayer'])
                                  )
            self.signal_update_game_stats.emit(str(message['arguments']['spinsExecuted']),
                                               str(message['arguments']['maxSpins']),
                                               str(message['arguments']['round']),
                                               str(message['arguments']['totalRounds']))
        if perform_ack_at_end is True:
            self.issueAck(message['action'])

    @pyqtSlot()
    def askToSpin(self):
        response = dict()
        response['action'] = "userInitiatedSpin"
        response['arguments'] = None
        self.signal_send_message.emit(json.dumps(response))

    @pyqtSlot(str)
    def returnCategory(self, string):
        response = dict()
        response['action'] = "responseCategorySelect"
        response['arguments'] = string
        self.signal_send_message.emit(json.dumps(response))

    def registerPlayer(self):
        """Ask Player what their name is"""
        # TODO: Prompt Players for their Names at the start of a game
        test_names = ["Aaron", "James", "Glenn", "Lorraine", "Markham"]
        r = random.randrange(0, len(test_names))
        return test_names[r]

    def issueAck(self, action):
        response = dict()
        response['action'] = action
        response['arguments'] = "ACK"
        self.signal_send_message.emit(json.dumps(response))

class HMI(QtWidgets.QMainWindow, Ui_MainWindow):

    signal_send_message = pyqtSignal(str)
    signal_temp_select_category = pyqtSignal(str)

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
        self.loglevel = loglevel

        self.MSG_controller = HMIMessageController(loglevel=loglevel)

        self.logic_controller = HMILogicController(loglevel=loglevel)
        self.logic_controller_thread = QThread(self)

        # Pass messages received to the logic controller
        self.MSG_controller.signal_recieve_message.connect(self.logic_controller.processMessage)

        # Pass responses from the logic controller into the output of the message controller
        self.logic_controller.signal_send_message.connect(self.MSG_controller.send_message)
        self.signal_send_message.connect(self.MSG_controller.send_message)

        # Pass requests from the logic controller to update game stats to the HMI engine
        self.logic_controller.signal_update_game_stats.connect(self.updateGameStats)

        # Pass requests from the logic controller to update player stats to the HMI engine
        self.logic_controller.signal_update_player_data.connect(self.updatePlayer)

        # Pass requests from the logic controller to spin the wheel to the HMI engine
        self.logic_controller.signal_spin_wheel.connect(self.spinWheel)

        # Pass requests from the logic controller to alter UI to indicate the name of winner
        self.logic_controller.signal_display_winner.connect(self.displayWinner)

        # Pass requests from the logic controller to prompt a user to select a category
        self.logic_controller.signal_select_category.connect(self.selectCategory)

        # temporarily, connect category stuff up
        self.signal_temp_select_category.connect(self.logic_controller.returnCategory)

        self.logic_controller.moveToThread(self.logic_controller_thread)

        self.logic_controller_thread.start()
        self.MSG_controller.start()

        self.doSpin.clicked.connect(self.logic_controller.askToSpin)

    def issuePrompt(self):
        pass

    @pyqtSlot(list)
    def selectCategory(self, categories):
        """Prompt user or opponents to select a category"""
        if isinstance(categories, list):
            if len(categories) <= 0:
                raise Exception("Category List does not include a sane value")
            else:
                # TODO: Implement UI for selecting from list of categories
                #prompt user with categories to select --
                self.signal_temp_select_category.emit(categories[random.randrange(0, len(categories))])

    @pyqtSlot()
    def selectOutcome(self):
        """Prompt players to indicate whether a response was correct or incorrect"""
        response = random.randrange(0, 2)
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

    @pyqtSlot(str, str, str, str)
    def updateGameStats(self, spinsExecuted, maxSpins, currentRound, totalRounds):
        spinString = spinsExecuted + "/" + maxSpins
        roundString = currentRound + "/" + totalRounds
        self.numSpins.setText(spinString)
        self.roundNumber.setText(roundString)

    @pyqtSlot(str, str, str, str, str)
    def updatePlayer(self, playerid, name, score, tokens, currentPlayer):
        # help with font: https://stackoverflow.com/questions/34398797/bold-font-in-label-with-setbold-method

        getattr(self, "player" + playerid + "Name").setText(name)
        highlight_font = QtGui.QFont()
        if currentPlayer == name:

            highlight_font.setBold(True)
            getattr(self, "player" + playerid + "Name").setFont(highlight_font)
        else:
            highlight_font.setBold(False)
            getattr(self, "player" + playerid + "Name").setFont(highlight_font)
        getattr(self, "player" + playerid + "Score").setText(score)
        getattr(self, "player" + playerid + "FT").setText(tokens)

    @pyqtSlot(str)
    def displayWinner(self, playername):
        self.labelWinner.setEnabled(True)
        self.winnerName.setText(playername)
        self.doSpin.setDisabled(True)