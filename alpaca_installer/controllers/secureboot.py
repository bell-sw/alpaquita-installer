#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import yaml
import os
from .controller import Controller
from alpaca_installer.views.secureboot import SecureBootView

class SecureBootController(Controller):
    def __init__(self, app):
        super().__init__(app)

        self._install_shim = False
        self._is_efi = self._app.is_efi()

    def make_ui(self):
        return SecureBootView(self, self._install_shim) if self._is_efi else None

    def done(self, install_shim):
        self._install_shim = install_shim
        self._app.next_screen()

    def cancel(self):
        self._app.prev_screen()

    def to_yaml(self):
        return yaml.dump({'install_shim_bootloader': self._install_shim})
