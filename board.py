#!/bin/env python3

import socket
import commsettings
import time
import threading

class Board:
    def __init__(self):
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Configure Socket to allow reuse of sessions in TIME_WAIT. Otherwise, "Address already in use" is encountered
        # Per suggestion on https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use/29217540
        # by ForceBru
        self.receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receiver.bind(("127.0.0.1", commsettings.BOARD_LISTEN))
        self.receiver.listen(2)
        print("Board: successfully opened", str(commsettings.BOARD_LISTEN))
        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                self.sender = socket.create_connection(("127.0.0.1", commsettings.GAME_BOARD_LISTEN))
                break
            except Exception as e:
                print(e)
                time.sleep(1)
                continue
        while True:
            client, src = self.receiver.accept()
            clienthandle = threading.Thread(target=self.handleInboundConnection, args=(client,))
            clienthandle.start()

    def handleInboundConnection(self, sock):
        command = sock.recv(1024)
        if command == 1:
            self.flipQuestion()
            self.sender.send("ACK")

    def flipQuestion(self, category):
        # Flip over the correct category card
        pass

    def getCommand(self):
        while True:
            try:
                time.sleep(0.1)
                command = self.receiver.recv(1024)
                if (command == 1):
                    self.flipQuestion()
                    self.sender.send("ACK")
                else:
                    continue
            except Exception as e:
                print("board:", e)

