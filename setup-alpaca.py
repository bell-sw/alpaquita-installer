#!/usr/bin/env python3

import logging

from app.application import Application
from app.palette import PALETTE

logging.basicConfig(filename='installer.log', filemode='w')

app = Application(header='Alpaca Linux Installation',
                  palette=PALETTE)
app.run()
