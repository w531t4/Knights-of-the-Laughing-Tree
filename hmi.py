#!/bin/env python3

import socket
import commsettings
import threading
import time
import messaging
import queue

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
                message = self.clientqueue.get()
                self.msg_controller.send_string(self.sender, "ACK")
            else:
                time.sleep(.1)

    def issuePrompt(self):
        pass
