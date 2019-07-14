#!/bin/env python3

from player import Player
from trivia import Trivia
import random
import socket

class WOJ:
    def __init__(self):
        self.players = []
        self.totalRounds = 2 # TODO: Review self.totalRounds
        self.round = -1
        self.spins = 0

        #game config
        # TODO: Alter Geometry
        self.geometry_width = 3
        self.geometry_height = 2

        # initialize trivia
        self.triviadb = Trivia(min_questions=self.geometry_height)

        if len(self.triviadb) < (self.totalRounds * self.geometry_width):
            raise Exception("Insufficient trivia exists to complete a game with", self.totalRounds, "rounds and",
                            " a geometry of width = ", self.geometry_width)

        self.current_trivia = []
        self.utilized_categories = []

        # Determine
        #   Potentially difficulty?
        #   How many players are playing?
        #   Gather information about each player?
        self.enrollPlayers()

        # Once players are registered, agree upon game terms
        self.configureGame()

        self.currentPlayerIndex = self.selectRandomFirstPlayer()

        self.wheel_receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.wheel_receiver.bind(("127.0.0.1", 10010))
        self.wheel_receiver.listen(2)

        self.board_receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.board_receiver.bind(("127.0.0.1", 10001))
        self.board_receiver.listen(2)

        self.hmi_receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hmi_receiver.bind(("127.0.0.1", 10002))
        self.hmi_receiver.listen(2)

        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                self.wheel_sender = socket.connect("127.0.0.1", 10000)
                break
            except:
                continue

        while True:
            try:
                self.board_sender = socket.connect("127.0.0.1", 10001)
                break
            except:
                continue

        while True:
            try:
                self.hmi_sender = socket.connect("127.0.0.1", 10002)
                break
            except:
                continue

        # Once all setup is completed, start the show
        self.startGame()

    def selectRandomFirstPlayer(self):
        return random.randrange(0,len(self.players))

    def getCurrentPlayer(self):
        return Player(self.players[self.currentPlayerIndex])

    def changeTurn(self):
        numPlayers = len(self.players)
        if self.currentPlayerIndex == numPlayers - 1:
                self.currentPlayerIndex = 0
        else:
                self.currentPlayerIndex += 1

    def enrollPlayers(self):
        # TODO: find num_players
        num_players = 3
        if num_players < 2:
            raise Exception("Game must be played with more than one person")

        for each in range(1, num_players):
            self.players.append(Player())

    def configureGame(self):
        # TODO: Adjustable Number of Rounds in Game (self.totalRounds)
        # TODO: Adjustable Difficulty
        # TODO: Adjustable Timeout for User Decisions
        # TODO: Adjustable Bankruptsy Behavior
        pass

    def changeRound(self):
        for player in self.players:
                player.archivePoints()
        self.round += 1

        #document the categories utilized so they aren't reused later
        for each in [x.category for x in self.current_trivia]:
            if each not in self.utilized_categories:
                self.utilized_categories.append(each)

        #record current board state
        self.current_trivia = self.triviadb.selectRandomCategories(self.geometry_width,
                                             n_questions_per_category=self.geometry_height,
                                             exclude=self.utilized_categories)

    def startGame(self):
        spinMap = {

            # borrowed idea for switch from
            # https://jaxenter.com/implement-switch-case-statement-python-138315.html

            0: self.pickRandomCategory,
            1: self.pickRandomCategory,
            2: self.pickRandomCategory,
            3: self.pickRandomCategory,
            4: self.pickRandomCategory,
            5: self.pickRandomCategory,
            6: self.pickLoseTurn,
            7: self.pickAccumulateFreeTurnToken,
            8: self.pickBecomeBankrupt,
            9: self.pickPlayersChoice,
            10: self.pickOpponentsChoice,
            11: self.pickDoublePlayerRoundScore

        }

        for round in range(0, self.totalRounds):
            self.changeRound()
            # ready player 1
            while self.spins < 50: # TODO: detect if any Q/A remain on board
                if self.round == (self.totalRounds - 1):
                    # TODO: Set point totals on all Q/A to double what they were in the first round
                    pass
                spinResult = self.doSpin()
                postSpinAction = spinMap.get(spinResult, lambda: "Out of Scope")
                postSpinAction()

        # TODO: Compare Points, Declare Victor

    def doSpin(self):
        # TODO: Generate random int as random_int
        random_int = 1
        self.spins += 1
        return random_int

    def pickCategoryHelper(self, category):
        # TODO: Resolve Question/Answer from dictionary
        # TODO: Display Question to Player
        # TODO: Prompt Players to determine if they're ready for the answer to be displayed
        # TODO: Display answer when prompted.
        # TODO: After displaying answer, display mechanism to indicate if the question was answered successfully
        # TODO: Alter Player Score according to whether the question was answered successfully or not
        # if (question answered successfully):
        #   increase player score
        #   pass
        # else:
        #   decrease player score
        #   self.changeTurn()
        pass

    def pickRandomCategory(self):
        # TODO: This is wrong! we need to randomly select the category to place on the wheel, otherwise this is like opponents choice.
        category = self.current_trivia[random.randrange(0, len(self.current_trivia))]['category']
        # if (
        # TODO: Check number of remaining questions for category
        # ) == 0:
        #           select a different available category (by Random)
        self.pickCategoryHelper(category)
        self.changeTurn()
        pass

    def pickLoseTurn(self):
        self.changeTurn()
        pass

    def pickAccumulateFreeTurnToken(self):
        self.getCurrentPlayer().addFreeTurnToken()
        self.changeTurn()
        pass

    def pickBecomeBankrupt(self):
        self.getCurrentPlayer().setScore(0)
        self.changeTurn()
        pass

    def pickPlayersChoice(self):
        # TODO: Facilitate Explicit Selection (by Current Player) of Category from those available as 'category'
        # if (
        # TODO: Check number of remaining questions for category
        # ) == 0:
        #           request selection of new category (by Current Player)
        category = "chicken&waffles"
        self.pickCategoryHelper(category)
        pass

    def pickOpponentsChoice(self):
        # TODO: Facilitate Explicitly Selection (by Opponents) of Category from those available as 'category'
        # if (
        # TODO: Check number of remaining questions for category
        # ) == 0:
        #           request selection of new category (by Opponents)
        category = "chicken&waffles"
        self.pickCategoryHelper(category)
        pass

    def pickDoublePlayerRoundScore(self):
        self.getCurrentPlayer().setScore(self.getCurrentPlayer().getRoundScore() * 2)
        self.changeTurn()
        pass
