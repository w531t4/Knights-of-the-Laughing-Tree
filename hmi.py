#!/bin/env python3

import socket
import commsettings
import threading
import time
import messaging
import queue
import json
import random


class HMI:
    def __init__(self):
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Configure Socket to allow reuse of sessions in TIME_WAIT. Otherwise, "Address already in use" is encountered
        # Per suggestion on https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use/29217540
        # by ForceBru
        self.receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receiver.bind(("127.0.0.1", commsettings.HMI_LISTEN))
        self.receiver.listen(2)
        print("HMI: successfully opened", str(commsettings.HMI_LISTEN))
        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                self.sender = socket.create_connection(("127.0.0.1", commsettings.GAME_HMI_LISTEN))
                break
            except Exception as e:
                print("hmi:", e)
                time.sleep(1)

                continue

        self.clientqueue = queue.Queue()
        self.msg_controller = messaging.Messaging(commsettings.MESSAGE_BREAKER, self.receiver, self.clientqueue, debug=True, name="HMI")
        self.logic_controller = threading.Thread(target=self.logic_controller)
        self.logic_controller.start()

    def logic_controller(self):
        while True:
            if not self.clientqueue.empty():
                try:
                    message = json.loads(self.clientqueue.get())
                except json.JSONDecodeError:
                    print ("HMI: Failed to decode Message")

                # Check for Sane Message
                if not isinstance(message, dict):
                    raise Exception("JSON Blob didn't resolve to a dictionary")
                if "action" not in message.keys():
                    raise Exception("Message does not possess action key")
                if "arguments" not in message.keys():
                    raise Exception("Message does not possess arguments key")

                #Proceed with performing actioning a message
                if message['action'] == "promptCategorySelectByUser":
                    response = dict()
                    response['action'] = "responseCategorySelect"
                    response['arguments'] = self.selectCategory(message['arguments'])
                    self.msg_controller.send_string(self.sender, json.dumps(response))
                elif message['action'] == "promptIncorrectCorrectResponse":
                    response = dict()
                    response['action'] = "responseQuestion"
                    response['arguments'] = self.selectOutcome()
                    self.msg_controller.send_string(self.sender, json.dumps(response))
                elif message['action'] == "displayQuestion":
                    response = dict()
                    self.displayQuestion(message['arguments'])
                    response['action'] = "displayQuestion"
                    response['arguments'] = "ACK"
                    self.msg_controller.send_string(self.sender, json.dumps(response))
                elif message['action'] == "promptPlayerRegistration":
                    response = dict()
                    response['action'] = "responsePlayerRegistration"
                    response['arguments'] = self.registerPlayer()
                    self.msg_controller.send_string(self.sender, json.dumps(response))
                else:
                    response = dict()
                    response['action'] = message['action']
                    response['arguments'] = "ACK"
                    self.msg_controller.send_string(self.sender, json.dumps(response))
            else:
                time.sleep(.1)

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

    def registerPlayer(self):
        """Ask Player what their name is"""
        # TODO: Prompt Players for their Names at the start of a game
        test_names = ["Aaron", "James", "Glenn", "Lorraine", "Markham"]
        r = random.randrange(0, len(test_names))
        return test_names[r]