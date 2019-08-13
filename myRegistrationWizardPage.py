from PyQt5 import QtWidgets, QtTest
from PyQt5.QtCore import pyqtSignal, pyqtSlot
import logging
import logs


class MyRegistrationWizardPage(QtWidgets.QWizardPage):
    signal_ask_for_validation = pyqtSignal()
    signal_validation_response_success = pyqtSignal()
    signal_validation_response_failure = pyqtSignal()

    def __init__(self, parent=None, loglevel=logging.DEBUG):
        super(MyRegistrationWizardPage, self).__init__(parent)
        self.validation_response = None
        self.signal_validation_response_failure.connect(self.response_failure)
        self.signal_validation_response_success.connect(self.response_success)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel

    def validatePage(self):
        self.signal_ask_for_validation.emit()
        while self.validation_response is None:
            # TODO: Magic Number
            QtTest.QTest.qWait(50)

        self.logger.debug("returning validation_response = " + str(self.validation_response))
        return self.validation_response

    @pyqtSlot()
    def response_success(self):
        self.logger.debug("set validation_response to True")
        self.validation_response = True

    @pyqtSlot()
    def response_failure(self):
        self.logger.debug("set validation_response to False")
        self.validation_response = False
