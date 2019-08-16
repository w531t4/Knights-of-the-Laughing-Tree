#!/bin/env python3

from player import Player
from trivia import Trivia, TriviaDB
from timeit import default_timer as timer
from game_controller import GameLogicController
from game_state import GameState
import commsettings
import messaging

import random
import socket
import queue
import time
import json
import logging
import logs
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread


class Game(QThread):
    signal_send_message = pyqtSignal(str)

    def __init__(self, parent=None, loglevel=logging.INFO):
        super(Game, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel

        self.players = []
        self.maxPlayers = 3
        self.minPlayers = 2
        self.totalRounds = 2 # TODO: Review self.totalRounds
        self.round = 0
        self.spins = 0

        self.state = GameState()
        self.ANSWER_TIMEOUT = 30
        self.maxSpins = 8 # TODO: Change back to 50
        # game config
        # TODO: Alter Geometry
        self.geometry_width = 3
        self.geometry_height = 3

        # Determine
        #   Potentially difficulty?
        #   How many players are playing?
        #   Gather information about each player?

        self.MSG_controller = messaging.MessageController(loglevel=loglevel,
                                               msg_controller_name="GameLogic",
                                               listen_port=commsettings.GAME_HMI_LISTEN,
                                               target_port=commsettings.HMI_LISTEN)
        self.logic_controller = GameLogicController(loglevel=loglevel)
        self.logic_controller_thread = QThread(self)

        # Pass messages received to the logic controller
        self.MSG_controller.signal_recieve_message.connect(self.logic_controller.processMessage)

        # Pass responses from the logic controller into the output of the message controller
        self.logic_controller.signal_send_message.connect(self.MSG_controller.send_message)
        self.signal_send_message.connect(self.MSG_controller.send_message)

        #connect logic controller to Game in order to register players
        self.logic_controller.signal_enroll_players.connect(self.enrollPlayers)

        #connect logic controller to Game in order to determine where a wheel should spin to
        self.logic_controller.signal_execute_spin.connect(self.doSpin)

        #connect logic controller to Game to pass category selection
        self.logic_controller.signal_process_category_selection.connect(self.pickCategoryHelper)

        #connect logic controller to Game to check the timeliness of player responses
        self.logic_controller.signal_check_timeliness_of_answer.connect(self.check_validity_of_response)

        #connect determination on successfull/unsuccessful answering of question to a processor in Game
        self.logic_controller.signal_process_question_results.connect(self.alterScoreBasedOnResults)

        #connect  free turn
        self.logic_controller.signal_spend_freeturn_token.connect(self.spendFreeTurnToken)

        self.logic_controller.moveToThread(self.logic_controller_thread)

        self.MSG_controller.start()
        while not self.MSG_controller.built:
            pass
        self.logic_controller_thread.start()

        self.triviadb = Trivia(loglevel=self.loglevel, min_questions=self.geometry_height)

        if len(self.triviadb) < (self.totalRounds * self.geometry_width):
            raise Exception("Insufficient trivia exists to complete a game with", self.totalRounds, "rounds and",
                            " a geometry of width = ", self.geometry_width)

        self.current_trivia = list()
        self.utilized_categories = []

        self.current_questionbundle = None

        self.currentPlayerIndex = None
        self.wheel_map = None
        #self.enrollPlayers()
        #self.currentPlayerIndex = self.selectRandomFirstPlayer()

        # Once all setup is completed, start the show
        #self.gameLoop()

        #self.hmi_receiver.close()

    def selectRandomFirstPlayer(self):
        """Return an index representing the position which will take the first turn"""
        self.logger.debug("Enter Function")
        return random.randrange(0, len(self.players))

    def getCurrentPlayer(self) -> Player:
        self.logger.debug("Enter Function")
        if len(self.players) > 0:
            return self.players[self.currentPlayerIndex]
        else:
            return None

    def changeTurn(self):
        """Alter player state """
        numPlayers = len(self.players)
        if self.currentPlayerIndex == numPlayers - 1:
            self.currentPlayerIndex = 0
        else:
            self.currentPlayerIndex += 1
        self.pushUpdateGameState()
        self.logic_controller.notifyConclusionOfTurn()

    @pyqtSlot(list)
    def enrollPlayers(self, playerList):
        """Determine number of users playing"""
        self.logger.debug("Start")
        try:
            self.checkSanityPlayerList(playerList)
        except Exception as e:
            self.logic_controller.notifyPlayerRegistrationFailure(e)
        else:
            for playerName in playerList:
                playerIndex = len(self.players)
                self.players.append(Player(id=playerIndex, name=playerName))
                self.pushUpdateGameState()
            self.logic_controller.issueAck("responsePlayerRegistration")
            self.currentPlayerIndex = self.selectRandomFirstPlayer()
            self.changeRound()

    def checkSanityPlayerList(self, playerList):
        if not isinstance(playerList, list):
            raise Exception("provided argument is not a list")
        elif len(set(playerList)) < len(playerList):
            raise Exception("provided list contains duplicate names")
        elif len(playerList) < self.minPlayers:
            raise Exception("not enough players")
        elif len(playerList) > self.maxPlayers:
            raise Exception("too many players")
        else:
            return

    def changeRound(self):
        """Progress GameState to the Next Round"""
        self.logger.info("Begin Round Change")
        for player in self.players:
            player.archivePoints()

        #document the categories utilized so they aren't reused later
        if type(self.current_trivia) != type([]):
            raise Exception("The type of self.current_trivia is not list")
        if len(self.current_trivia) <= 0 and self.round >= 1:
            raise Exception("The length of the current trivia db is not sufficient")

        self.round += 1
        if self.round <= self.totalRounds:
            self.logger.info("Changing round from " + str(self.round-1) + " to " + str(self.round))
            self.spins = 0
            for each in [x for x in self.current_trivia]:
                self.logger.debug("new category:", each)
                if each['category'] not in self.utilized_categories:
                    self.utilized_categories.append(each['category'])

            #record current board state
            self.current_trivia = self.triviadb.selectRandomCategories(self.geometry_width,
                                                 n_questions_per_category=self.geometry_height,
                                                 exclude=self.utilized_categories)

            self.wheel_map = self.build_map()
            if self.round == 1:
                self.current_triviaDB = TriviaDB(self.current_trivia, loglevel=self.loglevel, starting_value=100)
            else:
                self.current_triviaDB = TriviaDB(self.current_trivia, loglevel=self.loglevel, starting_value=200)

            self.logger.debug("self.current_trivia=" + str(self.current_trivia))
            self.logger.debug(str(self.wheel_map))
            self.pushUpdateGameState()
            self.logger.debug("Round Change Complete")
        else:
            self.logic_controller.notifyWinner(self.calculateWinner())


    def gameLoop(self):
        self.logger.info("Start Game Loop")

        for round in range(0, self.totalRounds):
            self.changeRound()
            # ready player 1
            self.logger.info("Begin Round" + str(self.round))

    def receive_ack(self, action, extra_test=True):
        while self.msg_controller.q.empty() and extra_test is True:
            pass
            time.sleep(.1)
        if not self.msg_controller.q.empty():
            response = self.msg_controller.q.get()
            if json.loads(response)['action'] != action:
                raise Exception("Expecting action=%s, received action=%s arguments=%s" %
                             (action,
                             json.loads(response)['action'],
                             json.loads(response)['arguments']))
            if json.loads(response)['arguments'] != "ACK":
                raise Exception("Expecting ACK to action=%s, received action=%s arguments=%s" %
                                (action,
                                 json.loads(response)['action'],
                                 json.loads(response)['arguments']))
            return response
        else:
            raise Exception("Queue was emptied prior to being serviced")

    def calculateWinner(self):
        winner = self.players[0].getName()
        winnerScore = 0
        for each in self.players:
            self.logger.debug("each.getGameScore()=" + str(each.getGameScore()))
            if each.getGameScore() > winnerScore:
                winner = each.getName()
                winnerScore = each.getGameScore()
        return winner

    @pyqtSlot()
    def doSpin(self):
        """Emulate 'Spin' and select a random number between 0-11"""

        spinMap = {

            # borrowed idea for switch from
            # https://jaxenter.com/implement-switch-case-statement-python-138315.html


            0: self.pickLoseTurn,
            1: self.pickAccumulateFreeTurnToken,
            2: self.pickBecomeBankrupt,
            3: self.pickPlayersChoice,
            4: self.pickOpponentsChoice,
            5: self.pickDoublePlayerRoundScore,
            6: self.pickRandomCategory,
            7: self.pickRandomCategory,
            8: self.pickRandomCategory,
            9: self.pickRandomCategory,
            10: self.pickRandomCategory,
            11: self.pickRandomCategory
        }
        if self.spins < self.maxSpins:
            random_int = random.randrange(0, self.geometry_width + 6)
            spinResult = random_int
            self.spins += 1
            self.logic_controller.notifyStartWheelSpin(random_int)

            self.logger.debug("Spin Result=" + str(spinResult))

            postSpinAction = spinMap.get(self.wheel_map.index(spinResult), lambda: "Out of Scope")
            if self.wheel_map.index(spinResult) < 6:
                postSpinAction()
            else:
                postSpinAction(self.wheel_map.index(spinResult))
            #self.receive_ack("spinWheel")
        else:
            self.changeRound()
        return random_int

    def build_map(self):
        random_list = list()
        while len(random_list) < (self.geometry_width + 6):
            randomint = random.randrange(0, (self.geometry_width + 6))
            if randomint not in random_list:
                random_list.append(randomint)
        return random_list

    def build_wheelboard(self):
        # 1 - 6 always represent static sectors, 7-n represent categorical columns
        # current_trivia = [a,b,c.. n]
        #           where a = {'category': 'blah', 'questions': [{q1: a1, q2: a2, .. qn, an}] }
        r = list()
        for each in range(0, 6):
            t = dict()
            t['index'] = self.wheel_map[each]
            t['type'] = "noncategory"
            if each == 0:
                t['name'] = "loseturn"
            elif each == 1:
                t['name'] = "accumulatefreeturn"
            elif each == 2:
                t['name'] = "bankrupt"
            elif each == 3:
                t['name'] = 'playerschoice'
            elif each == 4:
                t['name'] = "opponentschoice"
            else:
                t['name'] = "doublescore"
            r.append(t)
        for index, catobject in enumerate(self.current_trivia):
            t = dict()
            t['index'] = self.wheel_map[index+6]
            t['name'] = catobject['category']
            t['type'] = "category"
            t['questions'] = self.current_triviaDB.listRemainingQuestions(catobject['category'])
            t['valid_values'] = self.current_triviaDB.getListOfValues()
            r.append(t)

        return sorted(r, key = lambda i: i['index'])

    @pyqtSlot(str)
    def pickCategoryHelper(self, category):
        self.logger.debug("Start")
        self.current_questionbundle = self.current_triviaDB.getQuestion(category)
        self.timer_start = timer()
        self.logic_controller.notifyAskQuestion(self.current_questionbundle['question'],
                                                category=self.current_questionbundle['category'],
                                                value=self.current_questionbundle['value'],
                                                timeout=self.ANSWER_TIMEOUT,
                                                )

    @pyqtSlot(float)
    def check_validity_of_response(self, responseTime):
        delta = responseTime - self.timer_start
        if self.ANSWER_TIMEOUT >= delta:
            self.logic_controller.notifyShowAnswer(self.current_questionbundle['question'],
                                                   self.current_questionbundle['answer'],
                                                   self.current_questionbundle['category'],
                                                   self.current_questionbundle['value'],
                                                   )

        else:
            if self.getCurrentPlayer().getFreeTurnTokens() > 0:
                self.logic_controller.notifyRequestIntentOfFreeTokenUse()
            else:
                self.changeTurn()

    @pyqtSlot(bool)
    def alterScoreBasedOnResults(self, didPlayerAnswerCorrectly):
        if didPlayerAnswerCorrectly:
            self.getCurrentPlayer().addToScore(int(self.current_questionbundle['value']))
            self.changeTurn()
        else:
            # player answered incorrectly
            self.getCurrentPlayer().addToScore(-1 * int(self.current_questionbundle['value']))

            #they may want to use freeturn token, if they have one
            if self.getCurrentPlayer().getFreeTurnTokens() > 0:
                self.logic_controller.notifyRequestIntentOfFreeTokenUse()
            else:
                self.changeTurn()

    @pyqtSlot(bool)
    def spendFreeTurnToken(self, result):
        if result:
            self.getCurrentPlayer().spendFreeTurnToken()
        else:
            self.changeTurn()

    def pickRandomCategory(self, index):
        self.logger.debug("Start")
        self.logger.debug("index=" + str(index))
        category = self.current_trivia[index-6]['category']
        self.logger.debug("category=" + str(category))
        if len(self.current_triviaDB.listRemainingQuestions(category)) > 0:
            self.pickCategoryHelper(category)
        else:
            #do nothing, don't change turn - allow player to spin again
            pass

    def pickLoseTurn(self):
        self.logger.debug("Start")
        if self.getCurrentPlayer().getFreeTurnTokens() > 0:
            self.logic_controller.notifyRequestIntentOfFreeTokenUse()
        else:
            self.changeTurn()

    def pickAccumulateFreeTurnToken(self):
        self.logger.debug("Start")
        self.getCurrentPlayer().addFreeTurnToken()
        self.changeTurn()

    def pickBecomeBankrupt(self):
        self.logger.debug("Start")
        self.getCurrentPlayer().setScore(0)
        self.changeTurn()

    def pickPlayersChoice(self):
        # TODO: Facilitate Explicit Selection (by Current Player) of Category from those available as 'category'
        # if (
        # TODO: Check number of remaining questions for category
        # ) == 0:
        #           request selection of new category (by Current Player)
        self.logger.debug("Start")

        # TODO: Resolve Categories
        categorylist = self.current_triviaDB.getPlayableCategories()

        self.logic_controller.notifyCategorySelectionByPlayerRequest(categorylist)
       # while self.msg_controller.q.empty():
        #    pass
        #    time.sleep(.1)
        #response = self.msg_controller.q.get()
        ##responseCategorySelect
        ## TODO: Needs message['action'] sanity check
        #if json.loads(response)['arguments'] in message['arguments']:
        #    self.pickCategoryHelper(json.loads(response)['arguments'])
        #else:
        #    raise Exception("Response Category not from the allowed list")

    def pickOpponentsChoice(self):
        self.logger.debug("Start")

        # TODO: Resolve Categories
        categorylist = self.current_triviaDB.getPlayableCategories()

        self.logic_controller.notifyCategorySelectionByOpponentRequest(categorylist)

    def buildGameState(self):
        gameState = dict()
        gameState['round'] = self.round
        gameState['totalRounds'] = self.totalRounds
        gameState['players'] = [dict(x.renderStatus()) for x in self.players]
        gameState['spinsExecuted'] = self.spins
        gameState['maxSpins'] = self.maxSpins
        if len(self.players) > 0 and self.currentPlayerIndex is not None:
            gameState['currentPlayer'] = self.getCurrentPlayer().getName()
        else:
            gameState['currentPlayer'] = ""
        if self.wheel_map is not None:
            gameState['wheelboard'] = self.build_wheelboard()
        return gameState

    def pickDoublePlayerRoundScore(self):
        self.logger.debug("Start")
        self.getCurrentPlayer().setScore(self.getCurrentPlayer().getRoundScore() * 2)
        self.changeTurn()

    def pushUpdateGameState(self):
        self.logic_controller.notifyUpdateGameStats(self.buildGameState())