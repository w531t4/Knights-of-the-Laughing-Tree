#!/bin/env python3
import logging
import sys


def build_logger(mod, loglevel):
    # logging.basicConfig(stream=sys.stdout, level=loglevel)
    # Logging Initialization taken almost verbatim from https://docs.python.org/3.1/library/logging.html
    logger = logging.getLogger(mod)
    if not logger.hasHandlers():
        logger.setLevel(loglevel)

        # create console handler and set level to debug
        logger_ch = logging.StreamHandler(sys.stdout)
        logger.setLevel(loglevel)

        # create formatter
        logger_formatter = logging.Formatter("%(asctime)s [%(levelname)8s] %(name)15s:%(funcName)-27s - %(message)s")

        # add formatter to ch
        logger_ch.setFormatter(logger_formatter)

        # add ch to logger
        logger.addHandler(logger_ch)

    return logger
