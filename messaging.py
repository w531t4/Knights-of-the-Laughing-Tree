#!/bin/env python3

import sys
import logging
import logs
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import socket
import queue
import commsettings
import time


class Messaging(QThread):
    signal = pyqtSignal(str)

    def __init__(self, breaker, sock, q, parent=None, loglevel=logging.INFO, name="empty"):
        super(Messaging, self).__init__(parent)
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
        self.logger.debug("    Sent Message (" + str(message) + ")")
        sock.sendall("".join([message, self.breaker]).encode())


class MessageController(QThread):
    signal_recieve_message = pyqtSignal(str)

    def __init__(self, loglevel=logging.INFO, msg_controller_name="setme", listen_port=None, target_port=None):
        QThread.__init__(self)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel

        self.msg_controller_name = msg_controller_name
        self.listen_port = listen_port
        self.target_port = target_port

        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientqueue = queue.Queue()
        self.msg_controller = Messaging(commsettings.MESSAGE_BREAKER, self.receiver, self.clientqueue,
                                                                                loglevel=self.loglevel,
                                                                                name=self.msg_controller_name)
        self.built = True

    def run(self):
        # Configure Socket to allow reuse of sessions in TIME_WAIT. Otherwise, "Address already in use" is encountered
        # Per suggestion on https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use/29217540
        # by ForceBru
        self.receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receiver.bind(("127.0.0.1", self.listen_port))
        self.receiver.listen(2)
        self.logger.info("successfully opened port " + str(self.listen_port))
        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                self.sender = socket.create_connection(("127.0.0.1", self.target_port))
                break
            except Exception as e:
                self.logger.error(e)
                time.sleep(1)
                continue

        self.msg_controller.start()

        while True:
            if not self.clientqueue.empty():
                self.signal_recieve_message.emit(self.clientqueue.get())
            time.sleep(.1)

    @pyqtSlot(str)
    def send_message(self, msg):
        self.msg_controller.send_string(self.sender, msg)
