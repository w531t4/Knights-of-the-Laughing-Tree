#!/bin/env python3

import sys
import logging
import logs
from PyQt5.QtCore import QThread, pyqtSignal


class Messaging(QThread):
    signal = pyqtSignal(str)

    def __init__(self, breaker, sock, q, loglevel=logging.INFO, name="empty"):
        QThread.__init__(self)
        self.logger = logs.build_logger(name +".msg", loglevel)
        self.name = name
        self.breaker = breaker
        self.logprefix = self.name + ":"
        self.q = q
        self.sock = sock

    def run(self):
        """Responsible for handling new TCP connections and facilitating the reception of messages"""
        client, src = self.sock.accept()
        while True:
            message = self.recv_string(client)
            self.logger.debug("Received Message (" + str(message) + ")")
            self.q.put(message)

    def recv_string(self, sock):
        """Poll socket for message ending with self.breaker. Render Message"""
        message = ""
        while len(message.split(self.breaker)) < 2:
            command = sock.recv(1)
            if command:
                message += bytearray(command).decode()
            else:
                self.logger.warn("Client Disconnected")
                sys.exit(1)
        return message.split(self.breaker)[0]

    def send_string(self, sock, message):
        sock.sendall("".join([message, self.breaker]).encode())
