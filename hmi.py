#!/bin/env python3

import socket

    def __init__(self):
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver.bind(("127.0.0.1", 10002))
        self.receiver.listen(2)
        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                self.sender = socket.connect("127.0.0.1", 10012)
                break
            except:
                continue
        issuePrompt()

    def issuePrompt():
        pass
