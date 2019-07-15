#!/bin/env python3

import socket
import commsettings
import threading
import random
import time

class Wheel:
    def __init__(self):
        self.receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Configure Socket to allow reuse of sessions in TIME_WAIT. Otherwise, "Address already in use" is encountered
        # Per suggestion on https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use/29217540
        # by ForceBru
        self.receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receiver.bind(("127.0.0.1", commsettings.WHEEL_LISTEN))
        self.receiver.listen(2)
        print("Wheel: successfully opened", str(commsettings.WHEEL_LISTEN))
        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                self.sender = socket.create_connection(("127.0.0.1", commsettings.GAME_WHEEL_LISTEN))

                break
            except Exception as e:
                print(e)
                time.sleep(1)
                continue
        while True:
            client, src = self.receiver.accept()
            clienthandle = threading.Thread(target=self.handleInboundConnection, args=(client,))
            clienthandle.start()

        self.receiver.close()

    def handleInboundConnection(self, sock):
        command = sock.recv(1024)
        print("Wheel: received message (" + str(command) +")")
        if command == 0x00:
            self.sender.send(self.doSpin())

    def doSpin(self):
        """Emulate 'Spin' and select a random number between 0-11"""
        # TODO: Generate random int as random_int
        random_int = random.randrange(0, 12)
        return random_int

  #  def getCommand(self):
