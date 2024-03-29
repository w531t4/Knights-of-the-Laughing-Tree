#!/bin/env python3

import sys
import logging
import logs
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5 import QtTest
import socket
import commsettings
import queue


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
        self.doRun = True

    def run(self):
        """Responsible for handling new TCP connections and facilitating the reception of messages"""
        while True:
            try:
                client, src = self.sock.accept()
                break
            except:
                self.logger.debug("failed to open socket, retry")
        while self.doRun:
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

    def quit(self):
        self.doRun = False
        self.logger.debug("quitting")
        self.sock.close()
        super(Messaging, self).quit()


class MessageController(QThread):

    def __init__(self, loglevel=logging.INFO, msg_controller_name="setme", listen_port=None, target_port=None):
        QThread.__init__(self)
        self.logger = logs.build_logger(__name__+":" + msg_controller_name +".msgCtrl", loglevel)
        self.loglevel = loglevel

        self.msg_controller_name = msg_controller_name
        self.listen_port = listen_port
        self.target_port = target_port
        self.ready = False

        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientqueue = queue.Queue()
        self.msg_controller = Messaging(commsettings.MESSAGE_BREAKER, self.receiver, self.clientqueue,
                                                                                loglevel=self.loglevel,
                                                                                name=self.msg_controller_name)
        self.built = True

    def quit(self):
        self.logger.debug("quitting")
        self.msg_controller.quit()
        super(MessageController, self).quit()
    def build_listener(self):
        # Configure Socket to allow reuse of sessions in TIME_WAIT. Otherwise, "Address already in use" is encountered
        # Per suggestion on https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use/29217540
        # by ForceBru
        self.receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        while True:
            try:
                self.receiver.bind(("127.0.0.1", self.listen_port))
            except:
                continue
            else:
                self.receiver.listen(2)
                break
        self.logger.info("successfully opened port " + str(self.listen_port))

    def build_destination(self):
        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                self.sender = socket.create_connection(("127.0.0.1", self.target_port))

                break
            except Exception as e:
                self.logger.error(e)
                QtTest.QTest.qWait(1000)
        self.logger.debug("successfully built connection to %s" % self.target_port)
        self.ready = True

    def run(self):
        self.build_listener()
        self.build_destination()
        self.msg_controller.start()

    @pyqtSlot(str)
    def send_message(self, msg):
        while not self.ready:
            self.logger.debug("not ready to send_message")
            QtTest.QTest.qWait(50)
        self.msg_controller.send_string(self.sender, msg)


class HMIMessageController(MessageController):

    signal_recieve_message = pyqtSignal(str)

    def __init__(self, loglevel=logging.INFO, msg_controller_name="setme", listen_port=None, target_port=None):
        super(HMIMessageController, self).__init__(loglevel=loglevel,
                                                    msg_controller_name=msg_controller_name,
                                                    listen_port=listen_port,
                                                    target_port=target_port)

    def run(self):
        self.build_listener()
        self.build_destination()
        self.msg_controller.start()

        while True:
            if not self.clientqueue.empty():
                self.signal_recieve_message.emit(self.clientqueue.get())
            QtTest.QTest.qWait(100)
