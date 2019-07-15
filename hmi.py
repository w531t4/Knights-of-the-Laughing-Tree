#!/bin/env python3

import socket
import commsettings
import threading
import time

class HMI:
    def __init__(self):
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        while True:
            client, src = self.receiver.accept()
            clienthandle = threading.Thread(target=self.handleInboundConnection, args=(client,))
            clienthandle.start()

    def handleInboundConnection(self, sock):
        command = sock.recv(1024)
        if command == 1:
            self.sender.send(self.doSpin())

    def issuePrompt(self):
        pass
