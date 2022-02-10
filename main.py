import urwid

from installer.application import Application
from installer.palette import PALETTE


app = Application()
urwid.MainLoop(app.ui, PALETTE, pop_ups=True).run()
