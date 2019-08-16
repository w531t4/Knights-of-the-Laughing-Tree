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
import catselect
from functools import partial
from hmi_controller import HMILogicController


from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QObject, Qt
from PyQt5 import uic, QtGui, QtTest, QtWidgets

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

        self.MSG_controller = messaging.MessageController(loglevel=loglevel,
                                                   msg_controller_name="HMILogic",
                                                   listen_port=commsettings.HMI_LISTEN,
                                                   target_port=commsettings.GAME_HMI_LISTEN)

        self.registration_wizard = wizard.MyWizard(ui_file="register_user_wizard.ui", loglevel=self.loglevel)

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
        self.logic_controller.signal_playerselect_category.connect(partial(self.selectCategory, target="player"))
        self.logic_controller.signal_opponentselect_category.connect(partial(self.selectCategory, target="opponents"))

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

        #connect logic controller to wizard success/fail
        self.logic_controller.signal_feedback_registration_fail.connect(self.registration_wizard.pageUserEntry.signal_validation_response_failure)
        self.logic_controller.signal_feedback_registration_failmsg.connect(self.registration_wizard.setFeedback)
        self.logic_controller.signal_feedback_registration_success.connect(self.registration_wizard.pageUserEntry.signal_validation_response_success)
        self.registration_wizard.signal_submit_players.connect(self.logic_controller.notifyUserRegistration)

        #self.signal_determine_freeturn_spend.connect(self.determineFreeTurnSpend)
        self.freeTurnSkip.clicked.connect(self.logic_controller.notifyFreeTurnSkip)
        self.freeTurnSpend.clicked.connect(self.logic_controller.notifyFreeTurnSpend)

        self.logic_controller_thread.start()
        self.MSG_controller.start()

        self.doSpin.clicked.connect(self.logic_controller.askToSpin)

        self.button_incorrect.clicked.connect(self.logic_controller.notifyUnsuccesfullOutcome)
        self.button_correct.clicked.connect(self.logic_controller.notifySuccesfullOutcome)
        self.button_reveal.clicked.connect(self.logic_controller.notifyNeedAnswer)
        self.wheel_resting_place = None

        self.registration_wizard.signal_close.connect(self.close)

        self.logic_controller_thread.start()
        self.MSG_controller.start()

        self.registration_wizard.show()

        # Ensure registration wizard is focused on at startup. Without this, mainUI is focused
        # activateWindow() must be called first
        self.registration_wizard.activateWindow()
        self.registration_wizard.raise_()



    @pyqtSlot(list)
    def selectCategory(self, categories, target="player"):
        """Prompt user or opponents to select a category"""
        if isinstance(categories, list):
            if len(categories) <= 0:
                raise Exception("Category List does not include a sane value")
            else:
                self.cat_select = catselect.MyCatSelect(ui_file="select_category.ui",
                                                        loglevel=self.loglevel,
                                                        categories=categories,
                                                        audience=target)
                self.cat_select.signal_submit_category.connect(self.logic_controller.returnCategory)
                self.cat_select.show()

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
        for xpos, each in enumerate(category_list, 1):
            valid_values = each['valid_values']
            getattr(self, "label_board_col" + str(xpos) + "_row1").setText(str(each['name']))
            #self.logger.debug("category_list=%s" % (category_list))
            for ypos, value in enumerate(valid_values, 2):
                #ypos == enumerate starts at 0 + (row1 is category row), so it starts at 2. therefore ypos + 2. ugly.
                row_alias = getattr(self, "label_board_col" + str(xpos) + "_row" + str(ypos))
                if str(value) in each['questions']:
                    getattr(self, "label_board_col" + str(xpos) + "_row" + str(ypos)).setEnabled(True)
                    getattr(self, "label_board_col" + str(xpos) + "_row" + str(ypos)).setText(str(value))
                else:
                    getattr(self, "label_board_col" + str(xpos) + "_row" + str(ypos)).setEnabled(False)
                    getattr(self, "label_board_col" + str(xpos) + "_row" + str(ypos)).setText("")

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
                self.logger.debug("locking %s" % (each))
                getattr(self, each).setDisabled(True)
        if "unlock" in state.keys():
            unlock = state['unlock']
            for each in unlock:
                self.logger.debug("unlocking %s" % (each))
                getattr(self, each).setEnabled(True)
        if "clear_lcd" in state.keys():
            clear = state['clear_lcd']
            for each in clear:
                self.logger.debug("clear_lcd %s" % (each))
                getattr(self, each).display("")
        if "clear_textbox" in state.keys():
            clear = state['clear_textbox']
            for each in clear:
                self.logger.debug("clear_textbox %s" % (each))
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