#!/bin/env python3

import socket


def is_port_in_use(port):
    # credit https://stackoverflow.com/questions/2470971/fast-way-to-test-if-a-port-is-in-use-using-python
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def get_port(base_port: int) -> int:
    start_port = base_port
    while True:
        start_port += 1
        try:
            is_port_in_use(start_port)
        except:
            pass
        else:
            return start_port

MESSAGE_BREAKER="@#$@#$@#$!!!@sdkd!"
