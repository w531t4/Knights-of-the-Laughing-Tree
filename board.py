#!/bin/env python3

import socket
import commsettings
import time
import threading
import messaging
import queue
import json
import logging
import logs
from PyQt5.QtCore import QThread, pyqtSignal


class Board(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self, loglevel=logging.INFO):
        QThread.__init__(self)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        # Configure Socket to allow reuse of sessions in TIME_WAIT. Otherwise, "Address already in use" is encountered
        # Per suggestion on https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use/29217540
        # by ForceBru
        self.receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receiver.bind(("127.0.0.1", commsettings.BOARD_LISTEN))
        self.receiver.listen(2)
        self.logger.info("Successfully opened port " + str(commsettings.BOARD_LISTEN))
        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                self.sender = socket.create_connection(("127.0.0.1", commsettings.GAME_BOARD_LISTEN))
                break
            except Exception as e:
                self.logger.error(e)
                time.sleep(1)
                continue
        self.clientqueue = queue.Queue()
        self.msg_controller = messaging.Messaging(commsettings.MESSAGE_BREAKER, self.receiver, self.clientqueue, loglevel=self.loglevel, name="Board")
        self.logic_controller = threading.Thread(target=self.logic_controller)
        self.logic_controller.start()

    def logic_controller(self):
        while True:
            if not self.clientqueue.empty():
                try:
                    message = json.loads(self.clientqueue.get())
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
                    self.msg_controller.send_string(self.sender, json.dumps(response))
                else:
                    response = dict()
                    response['action'] = message['action']
                    response['arguments'] = "ACK"
                    self.msg_controller.send_string(self.sender, json.dumps(response))
            else:
                time.sleep(.1)

    def flipQuestion(self, category):
        # Flip over the correct category card
        pass
