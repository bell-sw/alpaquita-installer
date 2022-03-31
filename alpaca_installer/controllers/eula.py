from __future__ import annotations
from typing import TYPE_CHECKING
import os

import alpaca_installer
from .controller import Controller
from alpaca_installer.views.eula import EULAView

if TYPE_CHECKING:
    from alpaca_installer.app.application import Application


class EULAController(Controller):
    def __init__(self, app: Application):
        super().__init__(app)

        dir_path = os.path.abspath(os.path.realpath(alpaca_installer.__file__))
        dir_path = os.path.dirname(dir_path)
        with open(os.path.join(dir_path, 'EULA'), 'r') as file:
            self._content = file.read()

    def make_ui(self):
        return EULAView(self, self._content)

    def done(self):
        self._app.next_screen()

    def cancel(self):
        self._app.exit()