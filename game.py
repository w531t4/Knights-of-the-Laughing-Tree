#!/bin/env python3

from player import Player

class WOJ:
    def __init__(self):
        self.players = []

        # Determine
        #   Potentially difficulty?
        #   How many players are playing?
        #   Gather information about each player?
        self.enrollPlayers()

        # Once players are registered, agree upon game terms
        self.configureGame()

        # TODO: Randomly pick player order
        self.currentPlayerIndex = 0

        # Once all setup is completed, start the show
        self.startGame()

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
        # TODO: Adjustable Number of Rounds in Game
        # TODO: Adjustable Difficulty
        # TODO: Adjustable Timeout for User Decisions
        # TODO: Adjustable Bankruptsy Behavior
        pass


    def startGame(self):
        #ready player 1
        spinResult = self.doSpin()
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
        postSpinAction = spinMap.get(spinResult, lambda: "Out of Scope")
        postSpinAction()


    def doSpin(self):
        # TODO: Generate random int as random_int
        random_int = 1
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
        # TODO: Facilitate Random Selection of Category from those available as 'category'
        # if (
        # TODO: Check number of remaining questions for category
        # ) == 0:
        #           select a different available category (by Random)
        category = "chicken&waffles"
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
        # TODO: Facilitate Explicity Selection (by Opponents) of Category from those available as 'category'
        # if (
        # TODO: Check number of remaining questions for category
        # ) == 0:
        #           request selection of new category (by Opponents)
        category = "chicken&waffles"
        self.pickCategoryHelper(category)
        pass

    def pickDoublePlayerRoundScore(self):
        self.getCurrentPlayer().setScore(self.getCurrentPlayer().getScore() * 2)
        self.changeTurn()
        pass




