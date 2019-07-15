#!/bin/env python3

from player import Player
from trivia import Trivia
from wheel import Wheel
from board import Board

from hmi import HMI
import threading
import commsettings

import random
import socket

class WOJ:
    def __init__(self):
        self.debug = True
        self.players = []
        self.totalRounds = 2 # TODO: Review self.totalRounds
        self.round = -1
        self.spins = 0

        # game config
        # TODO: Alter Geometry
        self.geometry_width = 2
        self.geometry_height = 2

        # initialize trivia
        self.triviadb = Trivia(min_questions=self.geometry_height)

        if len(self.triviadb) < (self.totalRounds * self.geometry_width):
            raise Exception("Insufficient trivia exists to complete a game with", self.totalRounds, "rounds and",
                            " a geometry of width = ", self.geometry_width)

        self.current_trivia = list()
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

        # Configure Socket to allow reuse of sessions in TIME_WAIT. Otherwise, "Address already in use" is encountered
        self.wheel_receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.wheel_receiver.bind(("127.0.0.1", commsettings.GAME_WHEEL_LISTEN))
        self.wheel_receiver.listen(2)
        self.wheel = threading.Thread(target=Wheel)

        self.board_receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Configure Socket to allow reuse of sessions in TIME_WAIT. Otherwise, "Address already in use" is encountered
        self.board_receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.board_receiver.bind(("127.0.0.1", commsettings.GAME_BOARD_LISTEN))
        self.board_receiver.listen(2)
        self.board = threading.Thread(target=Board)

        self.hmi_receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Configure Socket to allow reuse of sessions in TIME_WAIT. Otherwise, "Address already in use" is encountered
        self.hmi_receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.hmi_receiver.bind(("127.0.0.1", commsettings.GAME_HMI_LISTEN))
        self.hmi_receiver.listen(2)
        self.hmi = threading.Thread(target=HMI)

        self.wheel.start()
        self.board.start()
        self.hmi.start()

        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                if self.debug: print("game: creating connection to wheel")
                self.wheel_sender = socket.create_connection(("127.0.0.1", commsettings.WHEEL_LISTEN))
                break
            except:
                continue

        while True:
            try:
                if self.debug: print("game: creating connection to board")
                self.board_sender = socket.create_connection(("127.0.0.1", commsettings.BOARD_LISTEN))
                break
            except:
                continue

        while True:
            try:
                if self.debug: print("game: creating connection to hmi")
                self.hmi_sender = socket.create_connection(("127.0.0.1", commsettings.HMI_LISTEN))
                break
            except:
                continue

        # Once all setup is completed, start the show
        self.startGame()

    def selectRandomFirstPlayer(self):
        """Return an index representing the position which will take the first turn"""
        return random.randrange(0, len(self.players))

    def getCurrentPlayer(self):
        return Player(self.players[self.currentPlayerIndex])

    def changeTurn(self):
        """Alter player state """
        numPlayers = len(self.players)
        if self.currentPlayerIndex == numPlayers - 1:
                self.currentPlayerIndex = 0
        else:
                self.currentPlayerIndex += 1

    def enrollPlayers(self):
        """Determine number of users playing"""
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
        """Progress GameState to the Next Round"""
        if self.debug: print("changeRound(): Start")
        for player in self.players:
            player.archivePoints()
        self.round += 1

        #document the categories utilized so they aren't reused later
        if type(self.current_trivia) != type([]):
            raise Exception("The type of self.current_trivia is not list")
        if len(self.current_trivia) <= 0 and self.round != 0:
            raise Exception("The length of the current trivia db is not sufficient")
        if self.debug: print(self.current_trivia)
        for each in [x for x in self.current_trivia]:
            if self.debug: print("each:", each)
            if each['category'] not in self.utilized_categories:
                self.utilized_categories.append(each['category'])

        #record current board state
        self.current_trivia = self.triviadb.selectRandomCategories(self.geometry_width,
                                             n_questions_per_category=self.geometry_height,
                                             exclude=self.utilized_categories)
        print("changeRound(): End")
    def startGame(self):
        if self.debug: print("startGame(): start")
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
            if self.debug: print("startGame(): performing Housekeeping")
            self.changeRound()
            # ready player 1
            while self.spins < 50: # TODO: detect if any Q/A remain on board
                if self.round == (self.totalRounds - 1):
                    # TODO: Set point totals on all Q/A to double what they were in the first round
                    pass
                spinResult = self.doSpin()
                print("spin value:",spinResult)
                postSpinAction = spinMap.get(spinResult, lambda: "Out of Scope")
                postSpinAction()

        # TODO: Compare Points, Declare Victor

    def pickCategoryHelper(self, category):
        # TODO: Resolve Question/Answer from dictionary
        # TODO: Display Question to Player
        # TODO: Prompt Players to determine if they're ready for the answer to be displayed
        # TODO: Display answer when prompted.
        # TODO: After displaying answer, display mechanism to indicate if the question was answered successfully
        # TODO: Alter Player Score according to whether the question was answered successfully or not
        if self.debug: print("pickCategoryHelper(): Start")
        # if (question answered successfully):
        #   increase player score
        #   pass
        # else:
        #   decrease player score
        #   self.changeTurn()
        pass

    def pickRandomCategory(self):
        if self.debug: print("pickRandomCategory(): Start")
        # TODO: This is wrong! we need to randomly select the category to place on the wheel, otherwise this is like opponents choice.
        print("type self.current_trivia=", type(self.current_trivia))
        random_number = random.randrange(0, len(self.current_trivia))
        print("random_number", random_number)
        category = self.current_trivia[random.randrange(0, len(self.current_trivia))]['category']
        # if (
        # TODO: Check number of remaining questions for category
        # ) == 0:
        #           select a different available category (by Random)
        self.pickCategoryHelper(category)
        self.changeTurn()
        pass

    def pickLoseTurn(self):
        if self.debug: print("pickLoseTurn(): Start")
        self.changeTurn()
        pass

    def pickAccumulateFreeTurnToken(self):
        if self.debug: print("pickAccumulateFreeTurnToken(): Start")
        self.getCurrentPlayer().addFreeTurnToken()
        self.changeTurn()
        pass

    def pickBecomeBankrupt(self):
        if self.debug: print("pickBecomeBankrupt(): Start")
        self.getCurrentPlayer().setScore(0)
        self.changeTurn()
        pass

    def pickPlayersChoice(self):
        # TODO: Facilitate Explicit Selection (by Current Player) of Category from those available as 'category'
        # if (
        # TODO: Check number of remaining questions for category
        # ) == 0:
        #           request selection of new category (by Current Player)
        if self.debug: print("pickPlayersChoice(): Start")
        category = "chicken&waffles"
        self.pickCategoryHelper(category)
        pass

    def pickOpponentsChoice(self):
        # TODO: Facilitate Explicit Selection (by Opponents) of Category from those available as 'category'
        # if (
        # TODO: Check number of remaining questions for category
        # ) == 0:
        #           request selection of new category (by Opponents)
        if self.debug: print("pickOpponentsChoice(): Start")
        category = "chicken&waffles"
        self.pickCategoryHelper(category)
        pass

    def pickDoublePlayerRoundScore(self):
        if self.debug: print("pickDoublePlayersRoundScore(): Start")
        self.getCurrentPlayer().setScore(self.getCurrentPlayer().getRoundScore() * 2)
        self.changeTurn()
        pass
