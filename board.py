#!/bin/env python3


import logging
import logs


class Board:
    def __init__(self, loglevel=logging.INFO):
        self.logger = logs.build_logger(__name__, loglevel)


    def flipQuestion(self, category):
        # Flip over the correct category card
        pass
