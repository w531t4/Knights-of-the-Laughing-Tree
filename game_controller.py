from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import logs
import logging
from timeit import default_timer as timer
import json


class GameLogicController(QObject):

    signal_send_message = pyqtSignal(str)
    signal_enroll_players = pyqtSignal(list)
    signal_execute_spin = pyqtSignal()
    signal_process_category_selection = pyqtSignal(str)
    signal_check_timeliness_of_answer = pyqtSignal(float)
    signal_process_question_results = pyqtSignal(bool)
    signal_spend_freeturn_token = pyqtSignal(bool)

    def __init__(self, parent=None, loglevel=logging.INFO):
        super(GameLogicController, self).__init__(parent)
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
        if message['action'] == "responsePlayerRegistration":
            perform_ack_at_end = False
            self.signal_enroll_players.emit(json.loads(message['arguments']))
        elif message['action'] == "userInitiatedSpin":
            perform_ack_at_end = False
            self.signal_execute_spin.emit()
        elif message['action'] == "responseCategorySelect":
            self.signal_process_category_selection.emit(message['arguments'])
        elif message['action'] == "revealAnswer":
            self.signal_check_timeliness_of_answer.emit(timer())
        elif message['action'] == "responseQuestion":
            # did the player answer correctly or not?
            self.signal_process_question_results.emit(message['arguments'])
        elif message['action'] == "userInitiatedFreeTurnTokenSpend":
            self.signal_spend_freeturn_token.emit(True)
        elif message['action'] == "userInitiatedFreeTurnTokenSkip":
            self.signal_spend_freeturn_token.emit(False)


        if perform_ack_at_end is True and message['arguments'] != "ACK":
            self.issueAck(message['action'])

        #TODO: Break out into a recv() function
        if message['arguments'] == "ACK":
            if message['action'] == "endSpin":
                pass
            #elif message['action'] == "responseQuestion":
            #    local_action = dict()
            #    local_action['unlock'] = ["doSpin"]
            #    local_action['lock'] = ["button_incorrect", "button_correct"]
            #    self.signal_lock_unlock.emit(local_action)

    def issueAck(self, action):
        response = dict()
        response['action'] = action
        response['arguments'] = "ACK"
        self.signal_send_message.emit(json.dumps(response))

    def notifyPlayerRegistrationFailure(self, msg):
        message = dict()
        message['action'] = "responsePlayerRegistration"
        # TODO: Perhaps a better structure for passing info back with Nack
        message['arguments'] = ":".join(["NACK", str(msg)])
        self.signal_send_message.emit(json.dumps(message))

    def notifyConclusionOfTurn(self):
        message = dict()
        message['action'] = "endSpin"
        message['arguments'] = None
        self.signal_send_message.emit(json.dumps(message))

    def notifyWinner(self, string):
        message = dict()
        message['action'] = "displayWinner"
        message['arguments'] = string
        self.signal_send_message.emit(json.dumps(message))

    def notifyStartWheelSpin(self, number):
        message = dict()
        message['action'] = "spinWheel"
        message['arguments'] = number
        self.signal_send_message.emit(json.dumps(message))

    def notifyCategorySelectionByPlayerRequest(self, categoryList):
        message = dict()
        message['action'] = "promptCategorySelectByUser"
        message['arguments'] = categoryList
        self.signal_send_message.emit(json.dumps(message))

    def notifyCategorySelectionByOpponentRequest(self, categoryList):
        message = dict()
        message['action'] = "promptCategorySelectByOpponent"
        message['arguments'] = categoryList
        self.signal_send_message.emit(json.dumps(message))

    def notifyRequestIntentOfFreeTokenUse(self):
        message = dict()
        message['action'] = "promptSpendFreeTurnToken"
        message['arguments'] = None
        self.signal_send_message.emit(json.dumps(message))

    def notifyAskQuestion(self, question, category, value, timeout=30):
        message = dict()
        message['action'] = "displayQuestion"
        arguments = dict()
        arguments['question'] = question
        arguments['category'] = category
        arguments['value'] = value
        arguments['timeout'] = timeout
        message['arguments'] = arguments
        self.signal_send_message.emit(json.dumps(message))

    def notifyShowAnswer(self, question, answer, category, value):
        message = dict()
        message['action'] = "displayAnswer"
        arguments = dict()
        arguments['question'] = question
        arguments['category'] = category
        arguments['value'] = value
        arguments['answer'] = answer
        message['arguments'] = arguments
        self.signal_send_message.emit(json.dumps(message))

    def notifyUpdateGameStats(self, stats):
        message = dict()
        message['action'] = "updateGameState"
        message['arguments'] = stats
        self.signal_send_message.emit(json.dumps(message))
