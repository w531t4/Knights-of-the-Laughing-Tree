#!/bin/env python3

import socket


class Player:
    def __init__(self, id=None, name=""):
        self.roundScore = 0
        self.gameScore = 0
        self.freeTurnTokens = 0
        self.name = name
        if id is None:
            raise Exception("Did not include ID while creating Player object. An ID must be provided.")
        else:
            self.id = id

    def addToScore(self, score):
        self.setScore(self.roundScore + int(score))

    def setScore(self, score):
        self.roundScore = score

    def getName(self):
        return self.name

    def getRoundScore(self):
        return self.roundScore

    def getGameScore(self):
        return self.gameScore

    def archivePoints(self):
        self.gameScore = self.gameScore + self.roundScore
        self.roundScore = 0

    def addFreeTurnToken(self):
        self.freeTurnTokens += 1

    def spendFreeTurnToken(self):
        if self.freeTurnTokens > 0:
            self.freeTurnTokens -= 1
        else:
            raise Exception("Player cannot spend freeTurnToken they do not have")

    def getFreeTurnTokens(self):
        return self.freeTurnTokens

    def renderStatus(self):
        output = dict()
        output['name'] = self.name
        output['gameScore'] = self.getGameScore()
        output['roundScore'] = self.getRoundScore()
        output['freeTurnTokens'] = self.freeTurnTokens
        output['id'] = self.id
        return dict(output)
