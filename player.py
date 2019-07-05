#!/bin/env python3

class Player:
    def __init__(self, name=""):
        self.roundScore = 0
        self.gameScore = 0
        self.freeTurnTokens = 0
        self.name = name

    def addToScore(self, score):
        self.setScore(self.roundScore + score)

    def setScore(self, score):
        self.roundScore = score

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
        if (self.freeTurnTokens > 1):
            self.freeTurnToken -= 1
        else:
            raise Exception("Player cannot spend freeTurnToken they do not have")



