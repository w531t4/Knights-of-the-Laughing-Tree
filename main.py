#!/bin/env python3

import sys
from game import WOJ


def main(debug_status):
    WOJ(debug_status)

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
    banner()
    try:
        if "debug" in sys.argv[1]:
            main(True)
        else:
            main(False)
    except:
        main(False)
