#!/bin/env python3


import logging
import logs

class Wheel:
    def __init__(self, loglevel=logging.INFO):
        self.logger = logs.build_logger(__name__, loglevel)
