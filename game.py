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


class Game:
    def __init__(self, loglevel=logging.INFO):
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel

        self.players = []
        self.maxPlayers = 3
        self.minPlayers = 2
        self.totalRounds = 2 # TODO: Review self.totalRounds
        self.round = 0
        self.spins = 0

        self.maxSpins = 8 # TODO: Change back to 50
        # game config
        # TODO: Alter Geometry
        self.geometry_width = 3
        self.geometry_height = 3
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

        self.hmi_receiver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Configure Socket to allow reuse of sessions in TIME_WAIT. Otherwise, "Address already in use" is encountered
        # Per suggestion on https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use/29217540
        # by ForceBru
        self.hmi_receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.hmi_receiver.bind(("127.0.0.1", commsettings.GAME_HMI_LISTEN))
        self.hmi_receiver.listen(2)
        self.hmi_receiver_queue = queue.Queue()
        self.msg_controller = messaging.Messaging(commsettings.MESSAGE_BREAKER,
                                                        self.hmi_receiver,
                                                        self.hmi_receiver_queue,
                                                        loglevel=self.loglevel,
                                                        name="HMI_rcv")
        self.msg_controller.start()

        # Keep trying to create the sender until the correct receiver has been created
        while True:
            try:
                self.logger.info("Building connection to HMI on port " + str(commsettings.HMI_LISTEN))
                self.hmi_sender = socket.create_connection(("127.0.0.1", commsettings.HMI_LISTEN))
                break
            except:
                self.logger.warning("Failed to open connection to HMI, retrying")
                time.sleep(.1)
                continue

        self.currentPlayerIndex = None
        self.wheel_map = None
        self.enrollPlayers()
        self.currentPlayerIndex = self.selectRandomFirstPlayer()

        # Once players are registered, agree upon game terms
        self.configureGame()

        # Once all setup is completed, start the show
        self.gameLoop()

        self.hmi_receiver.close()

    def selectRandomFirstPlayer(self):
        """Return an index representing the position which will take the first turn"""
        self.logger.debug("Enter Function")
        return random.randrange(0, len(self.players))

    def getCurrentPlayer(self):
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

    def enrollPlayers(self):
        """Determine number of users playing"""
        # TODO: find num_players
        num_players = 0
        done = False
        while done is False:
            current_player_names = [x.getName() for x in self.players]
            while self.msg_controller.q.empty():
                pass
                time.sleep(.1)
            response = json.loads(self.msg_controller.q.get())
            if response['action'] == "responsePlayerRegistration":
                playerList = json.loads(response['arguments'])
                try:
                    self.checkSanityPlayerList(playerList)
                except Exception as e:
                    message = dict()
                    message['action'] = "responsePlayerRegistration"
                    #TODO: Perhaps a better structure for passing info back with Nack
                    message['arguments'] = ":".join(["NACK", str(e)])
                    self.msg_controller.send_string(self.hmi_sender, json.dumps(message))
                else:
                    for playerName in playerList:
                        playerIndex=len(self.players)
                        self.players.append(Player(id=playerIndex, name=playerName))
                        num_players += 1
                        self.pushUpdateGameState()
                    message = dict()
                    message['action'] = "responsePlayerRegistration"
                    message['arguments'] = "ACK"
                    self.msg_controller.send_string(self.hmi_sender, json.dumps(message))
                    done = True

    def configureGame(self):
        # TODO: Adjustable Number of Rounds in Game (self.totalRounds)
        # TODO: Adjustable Difficulty
        # TODO: Adjustable Timeout for User Decisions
        # TODO: Adjustable Bankruptsy Behavior
        pass

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
        self.logger.info("Changing round from " + str(self.round-1) + " to " +  str(self.round))
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

        self.current_triviaDB = TriviaDB(self.current_trivia, loglevel=self.loglevel)

        self.logger.debug("self.current_trivia=" + str(self.current_trivia))
        self.logger.debug(str(self.wheel_map))

        self.pushUpdateGameState()
        self.logger.debug("Round Change Complete")

    def gameLoop(self):
        self.logger.info("Start Game Loop")
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
            while self.spins < self.maxSpins: # TODO: detect if any Q/A remain on board
                self.logger.debug("stats: totalSpins=" + str(self.spins) +
                                                    " round=" + str(self.round))
                if self.round == (self.totalRounds - 1):
                    # TODO: Set point totals on all Q/A to double what they were in the first round
                    pass
                #if self.debug: print("Game: Sending message to wheel")
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
                self.msg_controller.send_string(self.hmi_sender, json.dumps(message))
                self.receive_ack("endSpin")

        # TODO: Compare Points, Declare Victor
        for play in self.players:
            play.archivePoints()
        message = dict()
        message['action'] = "displayWinner"
        message['arguments'] = self.calculateWinner()
        self.msg_controller.send_string(self.hmi_sender, json.dumps(message))

    def receive_ack(self, action, extra_test=True):
        while self.msg_controller.q.empty() and extra_test is True:
            pass
            time.sleep(.1)
        if not self.msg_controller.q.empty():
            response = self.msg_controller.q.get()
            if json.loads(response)['action'] != action:
                raise Exception("Expecting action=" + action)
            if json.loads(response)['arguments'] != "ACK":
                raise Exception("Expecting ACK to action=" + action)
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

    def doSpin(self):
        """Emulate 'Spin' and select a random number between 0-11"""
        while self.msg_controller.q.empty():
            pass
            time.sleep(.1)
        response = self.msg_controller.q.get()
        if json.loads(response)['action'] != 'userInitiatedSpin':
            raise Exception("Was expecting user initiated spin, received " + str(json.loads(response)['action']))
        message = dict()
        message['action'] = "userInitiatedSpin"
        message['arguments'] = "ACK"
        self.msg_controller.send_string(self.hmi_sender, json.dumps(message))

        random_int = random.randrange(0, self.geometry_width + 6)

        message = dict()
        message['action'] = "spinWheel"
        message['arguments'] = random_int
        self.msg_controller.send_string(self.hmi_sender, json.dumps(message))
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
            r.append(t)

        return sorted(r, key = lambda i: i['index'])

    def pickCategoryHelper(self, category):
        # TODO: Resolve Question/Answer from dictionary
        # TODO: Display Question to Player
        # TODO: Prompt Players to determine if they're ready for the answer to be displayed
        # TODO: Display answer when prompted.
        # TODO: After displaying answer, display mechanism to indicate if the question was answered successfully
        # TODO: Alter Player Score according to whether the question was answered successfully or not
        self.logger.debug("Start")
        ANSWER_TIMEOUT = 30

        message = dict()
        message['action'] = "displayQuestion"
        question_answer = self.current_triviaDB.getQuestion(category)
        question_answer['timeout'] = ANSWER_TIMEOUT
        question_only = dict(question_answer)
        question_only.pop("answer")
        message['arguments'] = question_only
        self.msg_controller.send_string(self.hmi_sender, json.dumps(message))
        # kick off 30s timer

        start = timer()
        self.receive_ack("displayQuestion", extra_test=((timer()-start) < ANSWER_TIMEOUT))

        # wait for revealAnswer
        while self.msg_controller.q.empty() and ((timer()-start) < ANSWER_TIMEOUT):
            pass
            time.sleep(.1)
        if not self.msg_controller.q.empty():
            response = self.msg_controller.q.get()
            # TODO: Needs message['action'] sanity check
            if json.loads(response)['action'] != "revealAnswer":
                raise Exception("Expecting action type 'revealAnswer'")

            message = dict()
            message['action'] = "revealAnswer"
            message['arguments'] = "ACK"
            self.msg_controller.send_string(self.hmi_sender, json.dumps(message))

            message = dict()
            message['action'] = "displayAnswer"
            message['arguments'] = question_answer
            self.msg_controller.send_string(self.hmi_sender, json.dumps(message))

            self.receive_ack("displayAnswer")

            while self.msg_controller.q.empty():
                pass
                time.sleep(.1)
            response = self.msg_controller.q.get()
            # TODO: Needs message['action'] sanity check
            if json.loads(response)['action'] != "responseQuestion":
                raise Exception("Expecting action type 'responseQuestion' for ACK")
            if json.loads(response)['arguments'] is not False and json.loads(response)['arguments'] is not True:
                raise Exception("Expecting responseQuestion to contain either True or False only")

            if json.loads(response)['arguments'] is True:
                self.getCurrentPlayer().addToScore(int(question_answer['score']))
            else:
                self.getCurrentPlayer().addToScore(int(int(question_answer['score']) * -1))

            message = dict()
            message['action'] = "responseQuestion"
            message['arguments'] = "ACK"
            self.msg_controller.send_string(self.hmi_sender, json.dumps(message))

        else:
            #timer ran out
            pass
        self.changeTurn()

    def pickRandomCategory(self, index):
        self.logger.debug("Start")
        self.logger.debug("index=" + str(index))
        category = self.current_trivia[index-6]['category']
        self.logger.debug("category=" + str(category))
        if len(self.current_triviaDB.listRemainingQuestions(category)) > 0:
            self.pickCategoryHelper(category)
            self.changeTurn()
        else:
            #do nothing, don't change turn - allow player to spin again
            pass

    def pickLoseTurn(self):
        self.logger.debug("Start")
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

        message = dict()
        message['action'] = "promptCategorySelectByUser"
        message['arguments'] = categorylist
        self.msg_controller.send_string(self.hmi_sender, json.dumps(message))
        while self.msg_controller.q.empty():
            pass
            time.sleep(.1)
        response = self.msg_controller.q.get()
        # TODO: Needs message['action'] sanity check
        if json.loads(response)['arguments'] in message['arguments']:
            self.pickCategoryHelper(json.loads(response)['arguments'])
        else:
            raise Exception("Response Category not from the allowed list")

    def pickOpponentsChoice(self):
        # TODO: Facilitate Explicit Selection (by Opponents) of Category from those available as 'category'
        # if (
        # TODO: Check number of remaining questions for category
        # ) == 0:
        #           request selection of new category (by Opponents)
        self.logger.debug("Start")

        # TODO: Resolve Categories
        categorylist = self.current_triviaDB.getPlayableCategories()

        message = dict()
        message['action'] = "promptCategorySelectByOpponent"
        message['arguments'] = categorylist
        self.msg_controller.send_string(self.hmi_sender, json.dumps(message))
        while self.msg_controller.q.empty():
            pass
            time.sleep(.1)
        response = self.msg_controller.q.get()
        # TODO: Needs message['action'] sanity check
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
        self.msg_controller.send_string(self.hmi_sender, json.dumps(message))
        response = self.receive_ack("updateGameState")