#!/bin/env python3

import threading

class Messaging:
    def __init__(self, breaker, sock, q,  debug=False, name="empty"):
        self.name = name
        self.breaker = breaker
        self.debug = debug
        self.logprefix = "Messaging:" + self.name + ":"
        self.q = q
        self.sock = sock
        self.thread = threading.Thread(target=self.handleInboundConnection)
        self.thread.start()

    def handleInboundConnection(self):
        """Responsible for handling new TCP connections and facilitating the reception of messages"""
        client, src = self.sock.accept()
        while True:
            message = self.recv_string(client)
            print(self.logprefix, "received message (" + str(message) + ")")
            self.q.put(message)

    def recv_string(self, sock):
        """Poll socket for message ending with self.breaker. Render Message"""
        message = ""
        while len(message.split(self.breaker)) < 2:
            command = sock.recv(1)
            if command:
                message += bytearray(command).decode()
            else:
                raise Exception("Client Disconnected")
        return message.split(self.breaker)[0]

    def send_string(self, sock, message):
        sock.sendall("".join([message, self.breaker]).encode())
