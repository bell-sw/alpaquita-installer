import logging

from installer.application import Application
from installer.palette import PALETTE

logging.basicConfig(filename='installer.log', filemode='w')

app = Application(header='Alpaca Linux Installation',
                  palette=PALETTE)
app.run()
