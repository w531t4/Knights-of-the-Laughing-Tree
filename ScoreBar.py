from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal, pyqtSlot
import logs
import logging
from PlayerFrame import PlayerFrame


class ScoreBar(QtWidgets.QFrame, QtWidgets.QMainWindow):

    resized = pyqtSignal(float)

    def __init__(self, parent=None, loglevel=logging.DEBUG):
        super(ScoreBar, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
        #self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        #self.horizontalLayout.setObjectName("horizontalLayout")
        self.baseLayout = QtWidgets.QHBoxLayout(self)
        self.baseLayout.setObjectName("baseLayout")


        self.show()

    def getplayer(self, index: int) -> PlayerFrame:
        return getattr(self, "player%s" % (index))

    @pyqtSlot(list)
    def updatePlayers(self, playerList):
        for i, each in enumerate(playerList):
            self.logger.debug("self.baseLayout.count()=%s" % (self.baseLayout.count()))
            if self.baseLayout.count() <= i:
                # create widget
                setattr(self, "player%s" % (i), PlayerFrame(parent=self, ui_file="playerframe.ui", name=each['name']))
                getattr(self, "player%s" % (i)).setName(each['name'])
                getattr(self, "player%s" % (i)).setScore(each['gameScore'] + each['roundScore'])
                getattr(self, "player%s" % (i)).setFreeTurnTokens(each['freeTurnTokens'])
                if each['active']:
                    self.logger.debug("setting %s active" % each['name'])
                    getattr(self, "player%s" % (i)).setActive()
                else:
                    self.logger.debug("setting %s inactive" % each['name'])
                    getattr(self, "player%s" % (i)).setInactive()
                self.baseLayout.addWidget(getattr(self, "player%s" % (i)))

        for i, each in enumerate(playerList):
            #update widgets
            #self.player0.setName(each['name'])
            self.logger.debug("set playername = %s" % each['name'])
            getattr(self, "player%s" % (i)).setName(each['name'])
            getattr(self, "player%s" % (i)).setScore(each['gameScore'] + each['roundScore'])
            getattr(self, "player%s" % (i)).setFreeTurnTokens("FreeTurns: %s" % each['freeTurnTokens'])
            if each['active']:
                self.logger.debug("setting %s active" % each['name'])
                getattr(self, "player%s" % (i)).setActive()
            else:
                self.logger.debug("setting %s inactive" % each['name'])
                getattr(self, "player%s" % (i)).setInactive()


    def resizeEvent(self, event):
        self.resized.emit(self.height())
        return super(ScoreBar, self).resizeEvent(event)