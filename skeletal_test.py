#!/bin/env python3

from game import Game
from player import Player
from trivia import Trivia
from wheel import Wheel
from board import Board
from hmi import HMI

import threading
import commsettings
import messaging

import json
import queue
import socket
import time
import logging


def test():
        hmi_receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Configure Socket to allow reuse of sessions in TIME_WAIT. Otherwise, "Address already in use" is encountered
        # Per suggestion on https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use/29217540
        # by ForceBru
        hmi_receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        hmi_receiver.bind(("127.0.0.1", commsettings.GAME_HMI_LISTEN))
        hmi_receiver.listen(2)
        hmi_receiver_queue = queue.Queue()
        hmi_msg_controller = messaging.Messaging(commsettings.MESSAGE_BREAKER,
                                                        hmi_receiver,
                                                        hmi_receiver_queue,
                                                        loglevel=logging.INFO,
                                                        name="Game:hmi_receiver")
        hmi = threading.Thread(target=HMI)

        hmi.start()

        # Allow subsystems to spawn
        time.sleep(1)

        # Keep trying to create the sender until the correct receiver has been created

        while True:
            try:
                hmi_sender = socket.create_connection(("127.0.0.1", commsettings.HMI_LISTEN))
                break
            except:
                continue

        total_tests = 0
        passes = 0
        failures = 0

        print("\nTesting comm interface between Game Logic and HMI")
        test_number = 0

        while test_number < 3:
            categorylist = ["l33t","Aaron", "James" ]
            message = dict()
            message['action'] = "promptCategorySelectByUser"
            message['arguments'] = categorylist
            test_number += 1
            hmi_msg_controller.send_string(hmi_sender, json.dumps(message))
            while hmi_msg_controller.q.empty():
                pass
                time.sleep(.1)
            response = hmi_msg_controller.q.get()
            if json.loads(response)['arguments'] in message['arguments']:
                print("\tTest Number: " + str(test_number) + "\tSent: " + message['action'] + "\tReceived: " + json.loads(response)['arguments'] + "\tP/F: PASS")
                total_tests += 1
                passes += 1
            else:
                print("\tTest Number: " + str(test_number) + "\tSent: " + message['action'] + "\tReceived: " + json.loads(response)['arguments'] + "\tP/F: FAIL")
                total_tests += 1
                failures += 1

        while test_number < 5:
            message = dict()
            message['action'] = "updateGameState"
            message['arguments'] = {"round": 0, "totalRounds": 2, "players": [{"name": "Aaron", "gameScore": 0, "roundScore": 0, "freeTurnTokens": 0}], "spinsExecuted": 0, "maxSpins": 5}
            test_number += 1
            hmi_msg_controller.send_string(hmi_sender, json.dumps(message))
            while hmi_msg_controller.q.empty():
                pass
                time.sleep(.1)
            response = hmi_msg_controller.q.get()
            if json.loads(response)['arguments'] == "ACK":
                print("\tTest Number: " + str(test_number) + "\tSent: " + message['action'] + "\tReceived: " + json.loads(response)['arguments'] + "\tP/F: PASS")
                total_tests += 1
                passes += 1
            else:
                print("\tTest Number: " + str(test_number) + "\tSent: " + message['action'] + "\tReceived: " + json.loads(response)['arguments'] + "\tP/F: FAIL")
                total_tests += 1
                failures += 1

        message = dict()
        message['action'] = "spinWheel"
        message['arguments'] = 5
        test_number = 0

        while test_number < 5:
            test_number += 1
            hmi_msg_controller.send_string(hmi_sender, json.dumps(message))
            while hmi_msg_controller.q.empty():
                pass
                time.sleep(.1)
            response = hmi_msg_controller.q.get()

            if json.loads(response)['arguments'] != "ACK":
                print("\tTest Number: " + str(test_number) + "\tSent: " + message['action'] + "\tReceived: " + json.loads(response)['arguments'] + "\tP/F: FAIL")
                total_tests += 1
                failures += 1
            else:
                print("\tTest Number: " + str(test_number) + "\tSent: " + message['action'] + "\tReceived: " + json.loads(response)['arguments'] + "\tP/F: PASS")
                total_tests += 1
                passes += 1

        print("\nTesting comm interface between Game Logic and Board")
        test_number = 0

        while test_number < 3:
            test_number += 1
            message = dict()
            message['action'] = "promptCategorySelectByUser"
            message['arguments'] = "0"
            hmi_msg_controller.send_string(hmi_sender, json.dumps(message))
            while hmi_msg_controller.q.empty():
                pass
                time.sleep(.1)
            response = hmi_msg_controller.q.get()
            if json.loads(response)['action'] == "responseCategorySelect":
                print("\tTest Number: " + str(test_number) + "\tSent: " + message['action'] + "\tReceived: " + json.loads(response)['action'] + "\tP/F: PASS")
                total_tests += 1
                passes += 1
            else:
                print("\tTest Number: " + str(test_number) + "\tSent: " + message['action'] + "\tReceived: " + json.loads(response)['action'] + "\tP/F: FAIL")
                total_tests += 1
                failures += 1

        while test_number < 5:
            test_number += 1
            message = dict()
            message['action'] = "displayQuestionsByCategory"
            message['arguments'] = ""
            hmi_msg_controller.send_string(hmi_sender, json.dumps(message))
            while hmi_msg_controller.q.empty():
                pass
                time.sleep(.1)
            response = hmi_msg_controller.q.get()
            if json.loads(response)['arguments'] == "ACK":
                print("\tTest Number: " + str(test_number) + "\tSent: " + message['action'] + "\tReceived: " + json.loads(response)['arguments'] + "\tP/F: PASS")
                total_tests += 1
                passes += 1
            else:
                print("\tTest Number: " + str(test_number) + "\tSent: " + message['action'] + "\tReceived: " + json.loads(response)['arguments'] + "\tP/F: FAIL")
                total_tests += 1
                failures += 1

        print("\nTotal Tests: " + str(total_tests) + "\tSuccesses: " + str(passes) + "\tFailures: " + str(failures) + "\n")

def banner():

    print("")
    print("  _____    ___     ___    _____  ")
    print(" |_   _|  | __|   / __|  |_   _| ")
    print("   | |    | _|    \\__ \\    | |   ")
    print("  _|_|_   |___|   |___/   _|_|_  ")
    print("_|\"\"\"\"\"|_|\"\"\"\"\"|_|\"\"\"\"\"|_|\"\"\"\"\"| ")
    print("\"`-0-0-\'\"`-0-0-\'\"`-0-0-\'\"`-0-0-\' ")
    print("")

if __name__ == "__main__":
    banner()
    test()
