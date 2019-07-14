#!/bin/env python3

import socket

class Board:
    def __init__(self):
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver.bind(("127.0.0.1", 10001))
        self.receiver.listen(2)
        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                self.sender = socket.connect("127.0.0.1", 10011)
                break
            except:
                continue
        getCommand()

    def flipQuestion(self, category):
        # Flip over the correct category card
        pass

    def getCommand():
        while True:
            command = self.receiver.recv()
                if (command == 1):
                    flipQuestion()
                    self.sender.send("ACK")
                else:
                    continue
