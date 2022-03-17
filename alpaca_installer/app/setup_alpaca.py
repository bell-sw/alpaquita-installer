#!/usr/bin/env python3

import sys

def main():
    import logging
    from .application import Application
    from .palette import PALETTE

    logging.basicConfig(filename='installer.log', filemode='w')

    app = Application(header='Alpaca Linux Installation',
                      palette=PALETTE)
    app.run()

if __name__ == '__main__':
    sys.exit(main())