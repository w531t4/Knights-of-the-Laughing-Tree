#!/bin/env python3

import sys
import logging
from hmi import HMI
from game import Game
from PyQt5 import QtWidgets
import commsettings

import json
import argparse

def build_args(loglevel, initial_port, target_scenario):
    start_port = initial_port
    HMI_PORT = commsettings.get_port(start_port)
    GAME_PORT = commsettings.get_port(HMI_PORT)
    hmi_args = dict()
    game_args = dict()

    hmi_args['loglevel'] = loglevel
    game_args['loglevel'] = loglevel

    hmi_args['hmi_port'] = HMI_PORT
    game_args['hmi_port'] = HMI_PORT

    hmi_args['game_port'] = GAME_PORT
    game_args['game_port'] = GAME_PORT

    hmi_args['ui_file'] = "ui.ui"

    if target_scenario is not None:
        try:
            spins = json.loads(target_scenario)['spins']
        except:
            spins = None
        try:
            players = json.loads(target_scenario)['players']
        except:
            players = None
        try:
            options = json.loads(target_scenario)['options']
        except:
            options = None

        game_args['predetermined_spins'] = spins
        game_args['predetermined_players'] = players
        if options is not None:
            game_args['predetermined_startingplayer'] = options['setStartingPlayer'] if "setStartingPlayer" in options.keys() else None

            hmi_args['skip_userreg'] = options['skipUserRegistrationWizard'] if "skipUserRegistrationWizard" in options.keys() else False
            hmi_args['skip_spinanimation'] = options['skipSpinAction'] if "skipSpinAction" in options.keys() else False

    args = dict()
    args['hmi'] = hmi_args
    args['game'] = game_args
    return args

def main(loglevel=logging.INFO, target_scenario: str = ""):
    start_port = 10000
    args = build_args(loglevel,start_port, target_scenario)

    app = QtWidgets.QApplication(sys.argv)
    game_obj = Game(**args['game'])
    hmi_obj = HMI(**args['hmi'])

    game_obj.start()
    hmi_obj.show()
    sys.exit(app.exec_())

def banner():

    print("")
    print("  888       888 888                        888                .d888        888888                                                 888         ")
    print("  888   o   888 888                        888               d88P\"           \"88b                                                 888         ")
    print("  888  d8b  888 888                        888               888              888                                                 888         ")
    print("  888 d888b 888 88888b.   .d88b.   .d88b.  888       .d88b.  888888           888  .d88b.   .d88b.  88888b.   8888b.  888d888 .d88888 888  888")
    print("  888d88888b888 888 \"88b d8P  Y8b d8P  Y8b 888      d88\"\"88b 888              888 d8P  Y8b d88\"\"88b 888 \"88b     \"88b 888P\"  d88\" 888 888  888")
    print("  88888P Y88888 888  888 88888888 88888888 888      888  888 888              888 88888888 888  888 888  888 .d888888 888    888  888 888  888")
    print("  8888P   Y8888 888  888 Y8b.     Y8b.     888      Y88..88P 888              88P Y8b.     Y88..88P 888 d88P 888  888 888    Y88b 888 Y88b 888")
    print("  888P     Y888 888  888  \"Y8888   \"Y8888  888       \"Y88P\"  888              888  \"Y8888   \"Y88P\"  88888P\"  \"Y888888 888     \"Y88888  \"Y88888")
    print("                                                                            .d88P                   888                                    888")
    print("                                                                          .d88P\"                    888                               Y8b d88P")
    print("                                                                         888P\"                      888                                \"Y88P\" ")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Wheel of Jeopardy')
    parser.add_argument('--debug', action="store_true", default=False, help="Turn on debug verbosity")
    parser.add_argument('--scenariofile',
                        action="store",
                        help="specify a file containing a json scenario (see example_scenario.json)")

    args = parser.parse_args()
    banner()
    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    if args.scenariofile:
        with open(args.scenariofile, 'r') as f:
            scenario = f.read()
    else:
        scenario = ""

    main(loglevel=level, target_scenario=scenario)

