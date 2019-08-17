#!/bin/env python3

import socket

# credit https://stackoverflow.com/questions/2470971/fast-way-to-test-if-a-port-is-in-use-using-python
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

MESSAGE_BREAKER="@#$@#$@#$!!!@sdkd!"
