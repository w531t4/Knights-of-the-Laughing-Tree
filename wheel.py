#!/bin/env python3

import socket

class Wheel:
    def __init__(self):
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver.bind(("127.0.0.1", 10000))
        self.receiver.listen(2)
        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                self.sender = socket.connect("127.0.0.1", 10010)
                break
            except:
                continue
        getCommand()

    def doSpin(self):
        # yield a number in range?
        pass

    def getCommand():
        while True:
            command = self.receiver.recv()
                if (command == 1):
                    self.sender.send(doSpin())
                else:
                    continue
