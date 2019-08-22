#!/bin/env python3

from player import Player
from trivia import Trivia, TriviaDB
from timeit import default_timer as timer

import commsettings
import messaging

import random
import socket
import queue
import time
import json
import logging
import logs
from PyQt5.QtCore import QThread
from PyQt5 import QtTest


class Game(QThread):
    def __init__(self,
                 parent=None,
                 loglevel=logging.INFO,
                 hmi_port=None,
                 game_port=None,
                 predetermined_spins=None,
                 predetermined_players=None,
                 predetermined_startingplayer=None):
        super(Game, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
        self.hmi_port = hmi_port
        self.game_port = game_port
        self.logger.debug("selected hmi_port=%s" % (self.hmi_port))
        self.logger.debug("selected game_port=%s" % (self.game_port))

        self.predetermined_spins = queue.Queue()
        if predetermined_spins is not None:
            [self.predetermined_spins.put(x) for x in predetermined_spins]
        self.players = list()
        self.use_predetermined_players = False
        if predetermined_players is not None:
            self.logger.debug("using predetermined players")
            self.use_predetermined_players = True
            for playerName in predetermined_players:
                playerIndex = len(self.players)
                self.players.append(Player(id=playerIndex, name=playerName))
        self.use_predetermined_startingplayer = predetermined_startingplayer
        self.logger.debug("predetermined_startingplayer = %s" % predetermined_startingplayer)

    def run(self):
        self.maxPlayers = 3
        self.minPlayers = 2
        self.totalRounds = 2
        self.round = 0
        self.spins = 0
        self.delay_before_question = 2000

        self.maxSpins = 50

        # game config
        self.geometry_width = 6
        self.geometry_height = 5
        self.triviadb = Trivia(loglevel=self.loglevel, min_questions=self.geometry_height)

        if len(self.triviadb) < (self.totalRounds * self.geometry_width):
            raise Exception("Insufficient trivia exists to complete a game with", self.totalRounds, "rounds and",
                            " a geometry of width = ", self.geometry_width)

        self.current_trivia = list()
        self.utilized_categories = []

        # Determine
        #   Potentially difficulty?
        #   How many players are playing?
        #   Gather information about each player?

        self.MSG_controller = messaging.MessageController(loglevel=self.loglevel,
                                               msg_controller_name="GameLogic",
                                               listen_port=self.game_port,
                                               target_port=self.hmi_port)
        self.MSG_controller.start()

        self.currentPlayerIndex = None
        self.wheel_map = None
        if not self.use_predetermined_players:
            self.enrollPlayers()
        #self.logger.debug(self.players)
        if self.use_predetermined_startingplayer is None:
            self.currentPlayerIndex = self.selectRandomFirstPlayer()
        else:
            self.currentPlayerIndex = self.use_predetermined_startingplayer
        self.players[self.currentPlayerIndex].setActive()

        # Once all setup is completed, start the show
        self.gameLoop()

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
        prev_player = self.currentPlayerIndex
        self.players[self.currentPlayerIndex].setInactive()
        if self.currentPlayerIndex == numPlayers - 1:
                self.currentPlayerIndex = 0
        else:
                self.currentPlayerIndex += 1
        self.players[self.currentPlayerIndex].setActive()

        self.logger.debug("Changed player from %s (%s) to %s (%s)" % (self.players[prev_player].getName(),
                                                                      prev_player,
                                                                      self.players[self.currentPlayerIndex].getName(),
                                                                      self.currentPlayerIndex))
        self.pushUpdateGameState()

    def enrollPlayers(self):
        """Determine number of users playing"""
        # TODO: find num_players
        self.logger.debug("got here")
        num_players = 0
        done = False
        while done is False:
            current_player_names = [x.getName() for x in self.players]
            while self.MSG_controller.clientqueue.empty():
                QtTest.QTest.qWait(100)
            response = json.loads(self.MSG_controller.clientqueue.get())
            if response['action'] == "responsePlayerRegistration":
                playerList = json.loads(response['arguments'])
                try:
                    self.checkSanityPlayerList(playerList)
                except Exception as e:
                    message = dict()
                    message['action'] = "responsePlayerRegistration"
                    #TODO: Perhaps a better structure for passing info back with Nack
                    message['arguments'] = ":".join(["NACK", str(e)])
                    self.MSG_controller.send_message(json.dumps(message))
                else:
                    for playerName in playerList:
                        playerIndex=len(self.players)
                        self.players.append(Player(id=playerIndex, name=playerName))
                        num_players += 1
                        self.pushUpdateGameState()
                    message = dict()
                    message['action'] = "responsePlayerRegistration"
                    message['arguments'] = "ACK"
                    self.MSG_controller.send_message(json.dumps(message))
                    done = True

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
            self.current_triviaDB = TriviaDB(self.current_trivia, loglevel=self.loglevel, starting_price=100)
        else:
            self.current_triviaDB = TriviaDB(self.current_trivia, loglevel=self.loglevel, starting_price=200)

        self.logger.debug("self.current_trivia=" + str(self.current_trivia))
        self.logger.debug(str(self.wheel_map))

        self.pushUpdateGameState()
        self.logger.debug("Round Change Complete")

    def gameLoop(self):
        self.logger.info("Start Game Loop")
        #self.currentPlayerIndex = self.selectRandomFirstPlayer()
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

        for round in range(0, self.totalRounds):
            self.changeRound()
            # ready player 1
            self.logger.info("Begin Round" + str(self.round))
            while self.spins < self.maxSpins:
                self.logger.debug("stats: totalSpins=" + str(self.spins) +
                                                    " round=" + str(self.round))
                spinResult = self.doSpin()

                self.logger.debug("Spin Result=" + str(spinResult))

                postSpinAction = spinMap.get(self.wheel_map.index(spinResult), lambda: "Out of Scope")
                if self.wheel_map.index(spinResult) < 6:
                    postSpinAction()
                else:
                    postSpinAction(self.wheel_map.index(spinResult))
                self.pushUpdateGameState()
                message = dict()
                message['action'] = "endSpin"
                message['arguments'] = None
                self.MSG_controller.send_message(json.dumps(message))
                self.receive_ack("endSpin")

        for play in self.players:
            play.archivePoints()
        message = dict()
        message['action'] = "displayWinner"
        message['arguments'] = self.calculateWinner()
        self.MSG_controller.send_message(json.dumps(message))

    def receive_ack(self, action, extra_test=True):
        while self.MSG_controller.clientqueue.empty() and extra_test is True:
            QtTest.QTest.qWait(100)
        if not self.MSG_controller.clientqueue.empty():
            response = self.MSG_controller.clientqueue.get()
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
        scores = [x.getGameScore() for x in self.players]
        score_set = list(set(scores))
        score_set.sort()
        high_score = score_set[-1]

        winners = []
        for each in self.players:
            if each.getGameScore() == high_score:
                winners.append(each)

        if len(winners) > 1:
            return " & ".join([x.getName() for x in self.players])
        else:
            return winners[0].getName()

    def doSpin(self):
        """Emulate 'Spin' and select a random number between 0-11"""

        while self.MSG_controller.clientqueue.empty():

            QtTest.QTest.qWait(100)
        response = self.MSG_controller.clientqueue.get()
        if json.loads(response)['action'] != 'userInitiatedSpin':
            raise Exception("Was expecting user initiated spin, received " + str(json.loads(response)['action']))
        message = dict()
        message['action'] = "userInitiatedSpin"
        message['arguments'] = "ACK"
        self.MSG_controller.send_message(json.dumps(message))


        if self.predetermined_spins.empty():
            random_int = random.randrange(0, self.geometry_width + 6)
        else:
            function_to_index_map = {
                "pickLoseTurn": 0,
                "pickAccumulateFreeTurnToken": 1,
                "pickBecomeBankrupt": 2,
                "pickPlayersChoice": 3,
                "pickOpponentsChoice": 4,
                "pickDoublePlayerRoundScore": 5,
                "pickRandomCategory1": 6,
                "pickRandomCategory2": 7,
                "pickRandomCategory3": 8,
                "pickRandomCategory4": 9,
                "pickRandomCategory5": 10,
                "pickRandomCategory6": 11,
            }
            #roll 9
            #wheel_map = [5, 1, ** 9 **, 7, 0]
            #spinMap = {... 2: loseturnfunc, ...}
            desired_function = self.predetermined_spins.get()
            try:
                function_index = function_to_index_map[desired_function]
            except:
                raise Exception("Provided function call does not exist")
            random_int = self.wheel_map[function_index]

        message = dict()
        message['action'] = "spinWheel"
        message['arguments'] = random_int
        self.MSG_controller.send_message(json.dumps(message))
        self.spins += 1

        self.receive_ack("spinWheel")
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
            t['valid_prices'] = self.current_triviaDB.getListOfPrices()
            r.append(t)

        return sorted(r, key = lambda i: i['index'])

    def pickCategoryHelper(self, category):
        self.logger.debug("Start")
        ANSWER_TIMEOUT = 30

        message = dict()
        message['action'] = "displayQuestion"
        question_answer = self.current_triviaDB.getQuestion(category)
        question_answer['timeout'] = ANSWER_TIMEOUT
        question_answer['player'] = self.getCurrentPlayer().getName()
        question_only = dict(question_answer)
        question_only.pop("answer")
        message['arguments'] = question_only
        self.MSG_controller.send_message(json.dumps(message))
        # kick off 30s timer

        start = timer()
        self.receive_ack("displayQuestion", extra_test=((timer()-start) < ANSWER_TIMEOUT))

        # wait for revealAnswer
        doChangeTurn = True
        while self.MSG_controller.clientqueue.empty() and ((timer()-start) < ANSWER_TIMEOUT):
            QtTest.QTest.qWait(100)
        if not self.MSG_controller.clientqueue.empty():
            response = self.MSG_controller.clientqueue.get()
            if json.loads(response)['action'] != "revealAnswer":
                raise Exception("Expecting action type 'revealAnswer'")

            message = dict()
            message['action'] = "revealAnswer"
            message['arguments'] = "ACK"
            self.MSG_controller.send_message(json.dumps(message))

            message = dict()
            message['action'] = "displayAnswer"
            message['arguments'] = question_answer
            self.MSG_controller.send_message(json.dumps(message))

            self.receive_ack("displayAnswer")

            while self.MSG_controller.clientqueue.empty():
                QtTest.QTest.qWait(100)
            response = self.MSG_controller.clientqueue.get()
            if json.loads(response)['action'] != "responseQuestion":
                raise Exception("Expecting action type 'responseQuestion' for ACK")
            if json.loads(response)['arguments'] is not False and json.loads(response)['arguments'] is not True:
                raise Exception("Expecting responseQuestion to contain either True or False only")

            if json.loads(response)['arguments'] is True:
                self.getCurrentPlayer().addToScore(int(question_answer['score']))
            else:
                # User answered question incorrectly

                # Check to see if user has freeTurn tokens available
                if self.getCurrentPlayer().getFreeTurnTokens() > 0:
                    message = dict()
                    message['action'] = "promptSpendFreeTurnToken"
                    message['arguments'] = None
                    self.MSG_controller.send_message(json.dumps(message))

                    self.receive_ack("promptSpendFreeTurnToken")

                    correctResponseReceived = False
                    while not correctResponseReceived:
                        self.logger.debug("entered currectResponseReceived loop")
                        while self.MSG_controller.clientqueue.empty():
                            QtTest.QTest.qWait(100)
                        self.logger.debug("msg_controller queue is no longer empty")
                        response = self.MSG_controller.clientqueue.get()
                        if json.loads(response)['action'] == 'userInitiatedFreeTurnTokenSpend':
                            self.logger.debug("user indicated to spend ft token")
                            self.getCurrentPlayer().spendFreeTurnToken()
                            # user indicated to spend free turn token
                            correctResponseReceived = True
                            doChangeTurn = False
                            message = dict()
                            message['action'] = "userInitiatedFreeTurnTokenSpend"
                            message['arguments'] = "ACK"
                            self.MSG_controller.send_message(json.dumps(message))
                        elif json.loads(response)['action'] == 'userInitiatedFreeTurnTokenSkip':
                            self.logger.debug("user indicated to skip spending ft token")
                            # user declided to spend token, decrement score since they answered incorrectly
                            self.getCurrentPlayer().addToScore(int(int(question_answer['score']) * -1))
                            correctResponseReceived = True
                            message = dict()
                            message['action'] = "userInitiatedFreeTurnTokenSkip"
                            message['arguments'] = "ACK"
                            self.MSG_controller.send_message(json.dumps(message))
                        else:
                            raise Exception(
                                "Was expecting a decision on free token spending, received "
                                + str(json.loads(response)['action']))
                else:
                    self.getCurrentPlayer().addToScore(int(int(question_answer['score']) * -1))

            message = dict()
            message['action'] = "responseQuestion"
            message['arguments'] = "ACK"
            self.MSG_controller.send_message(json.dumps(message))

        else:
            #timer ran out
            pass
        if doChangeTurn:
            self.changeTurn()

    def pickRandomCategory(self, index):
        self.logger.debug("Start")
        QtTest.QTest.qWait(self.delay_before_question)
        self.logger.debug("index=" + str(index))
        category = self.current_trivia[index-6]['category']
        self.logger.debug("category=" + str(category))
        if len(self.current_triviaDB.listRemainingQuestions(category)) > 0:
            self.pickCategoryHelper(category)
        else:
            #do nothing, don't change turn - allow player to spin again
            pass

    def quit(self) -> None:
        self.logger.debug("quitting")
        self.MSG_controller.quit()
        super(Game, self).quit()

    def pickLoseTurn(self):
        self.logger.debug("Start")
        doChangeTurn = False
        if self.getCurrentPlayer().getFreeTurnTokens() > 0:
            message = dict()
            message['action'] = "promptSpendFreeTurnToken"
            message['arguments'] = None
            self.MSG_controller.send_message(json.dumps(message))

            self.receive_ack("promptSpendFreeTurnToken")

            correctResponseReceived = False
            while not correctResponseReceived:
                self.logger.debug("entered currectResponseReceived loop")
                while self.MSG_controller.clientqueue.empty():
                    QtTest.QTest.qWait(100)
                self.logger.debug("msg_controller queue is no longer empty")
                response = self.MSG_controller.clientqueue.get()
                if json.loads(response)['action'] == 'userInitiatedFreeTurnTokenSpend':
                    self.logger.debug("user indicated to spend ft token")
                    self.getCurrentPlayer().spendFreeTurnToken()
                    # user indicated to spend free turn token
                    correctResponseReceived = True
                    doChangeTurn = False
                    message = dict()
                    message['action'] = "userInitiatedFreeTurnTokenSpend"
                    message['arguments'] = "ACK"
                    self.MSG_controller.send_message(json.dumps(message))
                elif json.loads(response)['action'] == 'userInitiatedFreeTurnTokenSkip':
                    self.logger.debug("user indicated to skip spending ft token")
                    # user declided to spend token, decrement score since they answered incorrectly
                    doChangeTurn = True
                    correctResponseReceived = True
                    message = dict()
                    message['action'] = "userInitiatedFreeTurnTokenSkip"
                    message['arguments'] = "ACK"
                    self.MSG_controller.send_message(json.dumps(message))
                else:
                    raise Exception(
                        "Was expecting a decision on free token spending, received "
                        + str(json.loads(response)['action']))
        else:
            doChangeTurn = True
        if doChangeTurn:
            self.changeTurn()

    def pickAccumulateFreeTurnToken(self):
        self.logger.debug("Start")
        self.getCurrentPlayer().addFreeTurnToken()
        self.changeTurn()

    def pickBecomeBankrupt(self):
        self.logger.debug("Start")
        self.getCurrentPlayer().setScore(0)
        message = dict()
        message['action'] = "playerBecomesBankrupt"
        message['arguments'] = None
        self.MSG_controller.send_message(json.dumps(message))
        self.receive_ack("playerBecomesBankrupt")
        self.changeTurn()

    def pickPlayersChoice(self):
        self.logger.debug("Start")
        QtTest.QTest.qWait(self.delay_before_question)
        categorylist = self.current_triviaDB.getPlayableCategories()

        message = dict()
        message['action'] = "promptCategorySelectByUser"
        message['arguments'] = categorylist
        self.MSG_controller.send_message(json.dumps(message))
        while self.MSG_controller.clientqueue.empty():
            QtTest.QTest.qWait(100)
        response = self.MSG_controller.clientqueue.get()
        if json.loads(response)['arguments'] in message['arguments']:
            self.pickCategoryHelper(json.loads(response)['arguments'])
        else:
            raise Exception("Response Category not from the allowed list")

    def pickOpponentsChoice(self):
        self.logger.debug("Start")
        QtTest.QTest.qWait(self.delay_before_question)
        categorylist = self.current_triviaDB.getPlayableCategories()

        message = dict()
        message['action'] = "promptCategorySelectByOpponent"
        message['arguments'] = categorylist
        self.MSG_controller.send_message(json.dumps(message))
        while self.MSG_controller.clientqueue.empty():
            QtTest.QTest.qWait(100)
        response = self.MSG_controller.clientqueue.get()
        if json.loads(response)['arguments'] in message['arguments']:
            self.pickCategoryHelper(json.loads(response)['arguments'])
        else:
            raise Exception("Response Category not from the allowed list")

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
        message = dict()
        message['action'] = "updateGameState"
        message['arguments'] = self.buildGameState()
        self.MSG_controller.send_message(json.dumps(message))
        response = self.receive_ack("updateGameState")
