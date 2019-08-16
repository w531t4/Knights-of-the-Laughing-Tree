#!/bin/env python3
import logs
import logging


class GameState:

    def __init__(self, loglevel=logging.DEBUG):
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel

        self.state = "WAIT_FOR_SPIN"
        self.valid_states = [
            "WAIT_FOR_SPIN",
            "WAIT_FOR_CATEGORY_SELECTION",
            "WAIT_FOR_REVEAL_INDICATION",
            "WAIT_FOR_CORRECT_INCORRECT_INDICATION",
            "WAIT_FOR_FREETURN_SPEND_SELECTION",
            "CHANGE_TURN",
            "CHANGE_ROUND",
            "SPIN",
            "LOSE_TURN",
            "BANKRUPTCY",
            "EARN_FREETURN",
            "DOUBLE_SCORE",
            "OPPONENTS_CHOICE"
            "PLAYERS_CHOICE",
        ]

    def changeState(self, string) -> None:
        if self.isValid(self.state, string):
            self.state = string
        else:
            self.logger.debug("Invalid Transition %s -> %s" % (self.state, string))

    def isValid(self, string) -> bool:
        valid_transitions = [
            # Players Choice, Opponents Choice
            ("WAIT_FOR_SPIN",                           "WAIT_FOR_CATEGORY_SELECTION"),
            ("WAIT_FOR_CATEGORY_SELECTION",             "WAIT_FOR_REVEAL_INDICATION"),
            ("WAIT FOR REVEAL_INDICATION",              "WAIT_FOR_CORRECT_INCORRECT_INDICATION"),
            ("WAIT_FOR_CORRECT_INCORRECT_INDICATION",   "WAIT_FOR_FREETURN_SPEND_SELECTION"),
            ("WAIT_FOR_FREETURN_SPEND_SELECTION",       "WAIT_FOR_SPIN"),
            # Bankruptcy, Double Score, Earn FreeTurn
            ("WAIT_FOR_SPIN",                           "WAIT_FOR_SPIN"),
            # Lose Turn
            ("WAIT_FOR_SPIN",                           "WAIT_FOR_FREETURN_SPEND_SELECTION"),
            ("WAIT_FOR_FREETURN_SPEND_SELECTION",       "WAIT FOR SPIN"),
            # Spin selects any specific category
            ("WAIT_FOR_SPIN",                           "WAIT_FOR_REVEAL_INDICATION"),
            ("WAIT FOR REVEAL_INDICATION",              "WAIT_FOR_CORRECT_INCORRECT_INDICATION"),
            ("WAIT_FOR_CORRECT_INCORRECT_INDICATION",   "WAIT_FOR_FREETURN_SPEND_SELECTION"),
            ("WAIT_FOR_FREETURN_SPEND_SELECTION",       "WAIT_FOR_SPIN")
            ]
        if (self.state, string) in valid_transitions:
            return True
        else:
            return False