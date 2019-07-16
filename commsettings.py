#!/bin/env python3

WHEEL_LISTEN = 10000
BOARD_LISTEN = 10001
HMI_LISTEN = 10002
GAME_WHEEL_LISTEN = 10010
GAME_BOARD_LISTEN = 10011
GAME_HMI_LISTEN = 10012

MESSAGE_BREAKER="@#$@#$@#$!!!@sdkd!"
#wheel
#    binds on 10000
#    connects to 10010
#board
#    binds on 10001
#    connects to 10011
#hmi
#    binds on 10002
#    connects to 10012
#
#game:
#    binds on 10010 wheel
#    binds on 10011 board
#    binds on 10012 hmi
