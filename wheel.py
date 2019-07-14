#!/bin/env python3

import socket
import commsettings
import threading

class Wheel:
    def __init__(self):
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver.bind(("127.0.0.1", commsettings.WHEEL_LISTEN))
        self.receiver.listen(2)
        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                self.sender = socket.create_connection(("127.0.0.1", commsettings.GAME_WHEEL_LISTEN))
                break
            except Exception as e:
                print(e)
                continue
        while True:
            client, src = self.receiver.accept()
            clienthandle = threading.Thread(target=self.handleInboundConnection, args=(client,))
            clienthandle.start()

    def handleInboundConnection(self, sock):
        command = sock.recv(1024)
        if command == 1:
            self.sender.send(self.doSpin())

    def doSpin(self):
        # yield a number in range?
        pass

  #  def getCommand(self):
