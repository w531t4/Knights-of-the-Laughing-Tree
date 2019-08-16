from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
import logging
import logs
import json


class HMILogicController(QObject):

    signal_send_message = pyqtSignal(str)
    signal_update_game_stats = pyqtSignal(str, str, str, str)
    signal_update_player_data = pyqtSignal(str, str, str, str, str)
    signal_spin_wheel = pyqtSignal(int)
    signal_playerselect_category = pyqtSignal(list)
    signal_opponentselect_category = pyqtSignal(list)
    signal_display_winner = pyqtSignal(str)
    signal_update_wheel = pyqtSignal(list)
    signal_update_board = pyqtSignal(list)
    signal_display_question = pyqtSignal(dict)
    signal_display_answer = pyqtSignal(dict)
    signal_determine_correctness = pyqtSignal()
    signal_lock_unlock = pyqtSignal(dict)
    signal_start_timer = pyqtSignal(int)
    signal_stop_timer = pyqtSignal()
    signal_feedback_registration_fail = pyqtSignal()
    signal_feedback_registration_failmsg = pyqtSignal(str)
    signal_feedback_registration_success = pyqtSignal()
    signal_determine_freeturn_spend = pyqtSignal()

    def __init__(self, parent=None, loglevel=logging.INFO):
        super(HMILogicController, self).__init__(parent)
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
            self.signal_playerselect_category.emit(message['arguments'])
        elif message['action'] == "promptCategorySelectByOpponent":
            perform_ack_at_end = False
            self.signal_opponentselect_category.emit(message['arguments'])
        elif message['action'] == "promptIncorrectCorrectResponse":
            self.signal_determine_correctness.emit()
        elif message['action'] == "displayQuestion":
            perform_ack_at_end = False
            self.signal_display_question.emit(message['arguments'])
            # TODO: static value set here, needs to be sent in message
            self.signal_start_timer.emit(30)
        elif message['action'] == "responsePlayerRegistration":
            # cover ACK and NACK variants
            perform_ack_at_end = False
            if message['arguments'] == "ACK":
                self.signal_feedback_registration_success.emit()
            elif len(message['arguments']) > 3 and message['arguments'][0:4] == "NACK":
                self.signal_feedback_registration_fail.emit()
                self.signal_feedback_registration_failmsg.emit(message['arguments'].split(":")[1])
        elif message['action'] == "spinWheel":
            perform_ack_at_end = False
            self.signal_spin_wheel.emit(message['arguments'])
            local_action = dict()
            local_action['lock'] = ["doSpin", "button_correct", "button_incorrect",
                                    "button_reveal", "timer", "textbox_question",
                                    "textbox_answer", "freeTurnSkip", "freeTurnSpend"]
            local_action['clear_textbox'] = ["textbox_question", "textbox_answer"]
            self.logger.debug("issuing lock/unlock for spinWheel ACK")
            self.signal_lock_unlock.emit(local_action)
        elif message['action'] == "displayAnswer":
            self.signal_display_answer.emit(message['arguments'])
        elif message['action'] == "displayWinner":
            self.signal_display_winner.emit(message['arguments'])
        elif message['action'] == "endSpin":
            local_action = dict()
            local_action['unlock'] = ["doSpin"]
            local_action['lock'] = ['button_correct', 'button_incorrect', 'button_reveal']
            self.logger.debug("issuing lock/unlock for endSpin")
            self.signal_lock_unlock.emit(local_action)
        elif message['action'] == "promptSpendFreeTurnToken":
            local_action = dict()
            local_action['unlock'] = ["freeTurnSkip", "freeTurnSpend"]
            self.logger.debug("issuing lock/unlock for promptSpendFreeTurnToken")
            self.signal_lock_unlock.emit(local_action)
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
                self.logger.debug("issuing lock/unlock for responseQuestion ACK")
                self.signal_lock_unlock.emit(local_action)
            elif message['action'] == "revealAnswer":
                local_action = dict()
                local_action['lock'] = ["button_reveal", "timer"]
                local_action['clear_lcd'] = ["timer"]
                self.logger.debug("issuing lock/unlock for revealAnswer ACK")
                self.signal_lock_unlock.emit(local_action)
                self.signal_stop_timer.emit()
            elif message['action'] == "userInitiatedFreeTurnTokenSkip":
                local_action = dict()
                self.logger.debug("issuing lock/unlock for userInitiatedFreeTurnTokenSkip ACK")
                local_action['lock'] = ["freeTurnSkip", "freeTurnSpend"]
                self.signal_lock_unlock.emit(local_action)
            elif message['action'] == "userInitiatedFreeTurnTokenSpend":
                local_action = dict()
                self.logger.debug("issuing lock/unlock for userInitiatedFreeTurnTokenSpend ACK")
                local_action['lock'] = ["freeTurnSkip", "freeTurnSpend"]
                self.signal_lock_unlock.emit(local_action)
            elif message['action'] == "userInitiatedSpin":
                self.logger.debug("Processing ACK of userInitiatedSpin")
                local_action = dict()
                local_action['lock'] = ["doSpin", "button_correct", "button_incorrect",
                                        "button_reveal", "timer", "textbox_question",
                                        "textbox_answer", "freeTurnSkip", "freeTurnSpend"]
                local_action['clear_textbox'] = ["textbox_question", "textbox_answer"]
                self.logger.debug("issuing lock/unlock for userInitiatedSpin ACK")
                self.signal_lock_unlock.emit(local_action)
            elif message['action'] == "spinWheel":
                self.logger.debug("Processing ACK of userInitiatedSpin")


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

    @pyqtSlot(list)
    def notifyUserRegistration(self, playerList):
        response = dict()
        response['action'] = "responsePlayerRegistration"
        response['arguments'] = json.dumps(playerList)
        self.signal_send_message.emit(json.dumps(response))

    @pyqtSlot()
    def notifyFreeTurnSkip(self):
        response = dict()
        response['action'] = "userInitiatedFreeTurnTokenSkip"
        response['arguments'] = None
        self.signal_send_message.emit(json.dumps(response))

    @pyqtSlot()
    def notifyFreeTurnSpend(self):
        response = dict()
        response['action'] = "userInitiatedFreeTurnTokenSpend"
        response['arguments'] = None
        self.signal_send_message.emit(json.dumps(response))
