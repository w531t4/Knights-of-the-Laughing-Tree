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
from timeit import default_timer as timer
import wizard

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QObject, Qt
from PyQt5 import QtWidgets, uic, QtGui, QtTest, QtWidgets
from functools import partial


# We'll keep this during development as turning this off and ingesting the raw py allows for things like autocomplete
global IMPORT_UI_ONTHEFLY
# If this is set to False, ui.py must be manually updated by issuing pyuic5
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
    signal_update_wheel = pyqtSignal(list)
    signal_update_board = pyqtSignal(list)
    signal_display_question = pyqtSignal(dict)
    signal_display_answer = pyqtSignal(dict)
    signal_determine_correctness = pyqtSignal()
    signal_lock_unlock = pyqtSignal(dict)
    signal_start_timer = pyqtSignal(int)
    signal_stop_timer = pyqtSignal()

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

        #TODO: Break out into function
        perform_ack_at_end = True
        # Proceed with performing actioning a message
        if message['action'] == "promptCategorySelectByUser":
            perform_ack_at_end = False
            self.signal_select_category.emit(message['arguments'])
        elif message['action'] == "promptCategorySelectByOpponent":
            perform_ack_at_end = False
            self.signal_select_category.emit(message['arguments'])
        elif message['action'] == "promptIncorrectCorrectResponse":
            self.signal_determine_correctness.emit()
        elif message['action'] == "displayQuestion":
            perform_ack_at_end = False
            self.signal_display_question.emit(message['arguments'])
            # TODO: static value set here, needs to be sent in message
            self.signal_start_timer.emit(30)
        elif message['action'] == "promptPlayerRegistration":
            # TODO: Needs conversion to UI model
            perform_ack_at_end = False
            response = dict()
            response['action'] = "responsePlayerRegistration"
            response['arguments'] = self.registerPlayer()
            self.signal_send_message.emit(json.dumps(response))
        elif message['action'] == "spinWheel":
            perform_ack_at_end = False
            self.signal_spin_wheel.emit(message['arguments'])
        elif message['action'] == "displayAnswer":
            self.signal_display_answer.emit(message['arguments'])
            #self.signal_stop_timer.emit()
        elif message['action'] == "displayWinner":
            self.signal_display_winner.emit(message['arguments'])
        elif message['action'] == "endSpin":
            local_action = dict()
            local_action['unlock'] = ["doSpin"]
            local_action['lock'] = ['button_correct', 'button_incorrect', 'button_reveal']
            self.signal_lock_unlock.emit(local_action)
            #self.signal_stop_timer.emit()
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
            if "wheelboard" in message['arguments'].keys():
                self.signal_update_wheel.emit([x['name'] for x in message['arguments']['wheelboard']])
                cats = [x for x in message['arguments']['wheelboard'] if x['type'] == "category"]
                self.logger.debug("cats=" + str(cats))
                self.signal_update_board.emit(cats)


        if perform_ack_at_end is True and message['arguments'] != "ACK":
            self.issueAck(message['action'])

        #TODO: Break out into a recv() function
        if message['arguments'] == "ACK":
            if message['action'] == "responseQuestion":
                local_action = dict()
                local_action['unlock'] = ["doSpin"]
                local_action['lock'] = ["button_incorrect", "button_correct"]
                self.signal_lock_unlock.emit(local_action)
            elif message['action'] == "revealAnswer":
                local_action = dict()
                local_action['lock'] = ["button_reveal", "timer"]
                local_action['clear_lcd'] = ["timer"]
                self.signal_lock_unlock.emit(local_action)
                self.signal_stop_timer.emit()
            elif message['action'] == "userInitiatedSpin":
                self.logger.debug("Processing ACK of userInitiatedSpin")
                local_action = dict()
                local_action['lock'] = ["doSpin", "button_correct", "button_incorrect",
                                        "button_reveal", "timer", "textbox_question",
                                        "textbox_answer"]
                local_action['clear_textbox'] = ["textbox_question", "textbox_answer"]
                self.signal_lock_unlock.emit(local_action)
            elif message['action'] == "responseFinishedPlayerRegistration":
                pass


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

    @pyqtSlot()
    def notifySuccesfullOutcome(self):
        response = dict()
        response['action'] = "responseQuestion"
        response['arguments'] = True
        self.signal_send_message.emit(json.dumps(response))

    @pyqtSlot()
    def notifyUnsuccesfullOutcome(self):
        response = dict()
        response['action'] = "responseQuestion"
        response['arguments'] = False
        self.signal_send_message.emit(json.dumps(response))

    @pyqtSlot()
    def notifyNeedAnswer(self):
        response = dict()
        response['action'] = "revealAnswer"
        response['arguments'] = None
        self.signal_send_message.emit(json.dumps(response))

    @pyqtSlot()
    def notifyFinishUserReg(self):
        response = dict()
        response['action'] = "responseFinishedPlayerRegistration"
        response['arguments'] = None
        self.signal_send_message.emit(json.dumps(response))


class HMI(QtWidgets.QMainWindow, Ui_MainWindow):

    signal_send_message = pyqtSignal(str)
    signal_temp_select_category = pyqtSignal(str)
    signal_start_timer = pyqtSignal(int)

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

        # Pass requests form the logic controller to ask HMI to update the board
        self.logic_controller.signal_update_board.connect(self.updateBoard)

        # Pass requests from the logic controller to ask HMI to update the wheel
        self.logic_controller.signal_update_wheel.connect(self.updateWheel)

        # Pass requests from the logic controller to ask HMI to diplay a question
        self.logic_controller.signal_display_question.connect(self.displayQuestion)

        # Pass requests from the logic controller to prompt the user to indicate the outcome of the question
        self.logic_controller.signal_determine_correctness.connect(self.selectOutcome)

        # Pass requests from the logic controller to ask HMI to display the answer to a question
        self.logic_controller.signal_display_answer.connect(self.displayAnswer)

        # Pass requests from the logic controller to ask HMI to adjust various items
        self.logic_controller.signal_lock_unlock.connect(self.setUIState)

        # connect indicator to star timer
        self.logic_controller.signal_start_timer.connect(self.startTimer)

        # connect indicator to stop timer
        self.logic_controller.signal_stop_timer.connect(self.stopTimer)

        self.logic_controller.moveToThread(self.logic_controller_thread)


        self.logic_controller_thread.start()
        self.MSG_controller.start()

        self.doSpin.clicked.connect(self.logic_controller.askToSpin)
        #self.doSpin.clicked.connect(partial(self.doSpin.setDisabled, True))

        self.button_incorrect.clicked.connect(self.logic_controller.notifyUnsuccesfullOutcome)
        self.button_correct.clicked.connect(self.logic_controller.notifySuccesfullOutcome)

        self.button_reveal.clicked.connect(self.logic_controller.notifyNeedAnswer)
        #self.button_reveal.clicked.connect(partial(self.button_reveal.setDisabled, True))
        #self.button_reveal.clicked.connect(partial(self.doSpin.setDisabled, True))
        self.wheel_resting_place = None
        self.wiz = wizard.MyWizard(ui_file="register_user_wizard.ui", loglevel=self.loglevel)
        self.wiz.show()
        self.wiz.exec_()

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
        self.button_correct.setEnabled(True)
        self.button_incorrect.setEnabled(True)


    @pyqtSlot(dict)
    def displayQuestion(self, question_dict):
        """Render provided question to display"""

        self.textbox_question.setEnabled(True)
        self.textbox_question.setText(question_dict['question'])
        self.button_reveal.setEnabled(True)
        self.logic_controller.issueAck("displayQuestion")

    @pyqtSlot(dict)
    def displayAnswer(self, question_dict):
        """Render provided question to display"""
        self.textbox_answer.setText(question_dict['answer'])
        self.textbox_answer.setEnabled(True)
        self.timer.setEnabled(False)
        self.timer.setDigitCount(2)
        self.button_correct.setEnabled(True)
        self.button_incorrect.setEnabled(True)

    @pyqtSlot(int)
    def spinWheel(self, destination):
        """ Make the Wheel Spin. Ensure it lands on Destination"""
        self.doSpin.setDisabled(True)

        num_sectors = 0
        for each in range(0, 12):
            if getattr(self, "label_wheel_" + str(each)).isEnabled():
                num_sectors += 1

        if self.wheel_resting_place is None:
            self.wheel_resting_place = 0
        last = self.wheel_resting_place

        def cycle(start_number, delay_ms, num_switches, sectors, target=None):
            number = start_number
            delay_ms = delay_ms/5
            if start_number > 0:
                last = start_number - 1
            else:
                last = sectors - 1
            for each in range(number, num_switches):
                each = each % sectors
                if last is not None:
                    getattr(self, "label_wheel_" + str(last)).setAlignment(Qt.AlignLeft)
                getattr(self, "label_wheel_" + str(each)).setAlignment(Qt.AlignRight)
                number = each
                last = each
                if number == target and target is not None:
                    return number
                QtTest.QTest.qWait(delay_ms)
            return number

        #num_sectors = 8
        self.wheel_resting_place = cycle(last, 15, num_sectors*10, num_sectors)
        self.wheel_resting_place = cycle(self.wheel_resting_place, 30, num_sectors*5, num_sectors)
        self.wheel_resting_place = cycle(self.wheel_resting_place, 45, num_sectors*3, num_sectors)
        self.wheel_resting_place = cycle(self.wheel_resting_place, 70, num_sectors*2, num_sectors)
        self.wheel_resting_place = cycle(self.wheel_resting_place, 140, num_sectors*2, num_sectors)
        self.wheel_resting_place = cycle(self.wheel_resting_place, 140, num_sectors*2, num_sectors, target=int(destination))


        #self.doSpin.setEnabled(True)
        #TODO: The HMI interface shouldn't directly trigger ACK's
        self.logic_controller.issueAck("spinWheel")
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

    @pyqtSlot(list)
    def updateWheel(self, sector_list):
        for i, each in enumerate(sector_list):
            sector_alias = getattr(self, "label_wheel_" + str(i))
            # TODO: This breaks the rules. hmi shouldn't know anything about the protocol
            if each == "bankrupt":
                sector_alias.setStyleSheet('background-color: black; color: white')
            elif each == "loseturn":
                sector_alias.setStyleSheet("")
            elif each == "accumulatefreeturn":
                sector_alias.setStyleSheet("")
            elif each == 'playerschoice':
                sector_alias.setStyleSheet("")
            elif each == "opponentschoice":
                sector_alias.setStyleSheet("")
            elif each == "doublescore":
                sector_alias.setStyleSheet("")
                #sector_alias.setStylesheet("background-color:#ff0000;")
            sector_alias.setText(each)
        num_sectors = len(sector_list)
        if num_sectors != 12:
            for each in range(num_sectors, 12):
                getattr(self, "label_wheel_" + str(each)).setDisabled(True)

    @pyqtSlot(list)
    def updateBoard(self, category_list):
        for i, each in enumerate(category_list):
            getattr(self, "label_board_col" + str(i+1) + "_row1").setText(str(each['name']))
            #self.logger.debug("set header_alias=" + each['name'])
            for j, score in enumerate([200, 400, 600, 800, 1000]):
                row_alias = getattr(self, "label_board_col" + str(i+1) + "_row" + str(j+2))
                if str(score) in each['questions']:
                    getattr(self, "label_board_col" + str(i + 1) + "_row" + str(j + 2)).setEnabled(True)
                    getattr(self, "label_board_col" + str(i + 1) + "_row" + str(j + 2)).setText(str(score))
                else:
                    getattr(self, "label_board_col" + str(i + 1) + "_row" + str(j + 2)).setEnabled(False)
                    getattr(self, "label_board_col" + str(i + 1) + "_row" + str(j + 2)).setText("")

    @pyqtSlot(str)
    def displayWinner(self, playername):
        self.labelWinner.setEnabled(True)
        self.winnerName.setText(playername)
        self.doSpin.setDisabled(True)

    @pyqtSlot(dict)
    def setUIState(self, state):
        if not isinstance(state, dict):
            raise Exception("was expecting state of type dict, received %s" % (str(type(state))))
        if "lock" in state.keys():
            lock = state['lock']
            for each in lock:
                getattr(self, each).setDisabled(True)
        if "unlock" in state.keys():
            unlock = state['unlock']
            for each in unlock:
                getattr(self, each).setEnabled(True)
        if "clear_lcd" in state.keys():
            clear = state['clear_lcd']
            for each in clear:
                getattr(self, each).display("")
        if "clear_textbox" in state.keys():
            clear = state['clear_textbox']
            for each in clear:
                getattr(self, each).setText("")
                pass

    @pyqtSlot(int)
    def startTimer(self, i):
        self.logger.debug("Start")
        self.timer_obj = MyTimer(loglevel=self.loglevel)
        self.timer_thread = QThread(self)
        self.timer.setEnabled(True)
        # Pass messages received to the logic controller
        self.signal_start_timer.connect(self.timer_obj.count_down)
        self.timer_obj.signal_update_timer.connect(self.updateTimer)
        self.timer_obj.moveToThread(self.timer_thread)
        self.timer_thread.start()
        self.signal_start_timer.emit(i)

    @pyqtSlot(str)
    def updateTimer(self, string):
        self.timer.setDigitCount(len(str(float(string))))
        self.timer.display(string)

    @pyqtSlot()
    def stopTimer(self):
        self.timer.setDisabled(True)
        self.timer_obj.stop()


class MyTimer(QObject):

    signal_update_timer = pyqtSignal(str)

    def __init__(self, loglevel=logging.INFO):
        QObject.__init__(self)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
        self._running = True

    @pyqtSlot(int)
    def count_down(self, i):
        t = timer()
        self.logger.debug("timer = " + str(t))
        self.logger.debug("timer - t=" + str(timer() - t))
        while (timer() - t) < i and self._running is True:
            delta = str(i - (timer() - t))
            before = delta.split(".")[0]
            after = delta.split(".")[1][0]
            new_time = str(before) + "." + str(after)
            self.signal_update_timer.emit(new_time)
            #TODO: Magic Number
            QtTest.QTest.qWait(50)

    def stop(self):
        # tip from https://stackoverflow.com/questions/51135444/how-to-kill-a-running-thread
        self._running = False


# UI Arrangements
# 1: Wait for user spin
# 2: Wait for user reveal
# 3: Wait for user to indicate correct/incorrect
# 4: Wait for user to indicate if they wish to spend freeturn token
# 5: Wait for user to select category
# 6: Wait for opponnent to select category