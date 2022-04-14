#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

from __future__ import annotations
from typing import TYPE_CHECKING

import urwid

from subiquitycore.ui.stretchy import Stretchy
from subiquitycore.ui.buttons import ok_btn
from subiquitycore.ui.utils import button_pile

from alpaca_installer.controllers.storage import StorageController

if TYPE_CHECKING:
    from .application import ApplicationUI


class HelpMsgStretchy(Stretchy):
    MSG = """
Welcome to the Alpaca Linux Installer!

This program will guide you through all the steps to install Alpaca Linux on one of your disks.

The procedure requires a disk minimum of {:.1f} GB size and an active network connection to the Internet or a private repository with APK packages.

Additional shell sessions are available on other virtual terminals. You can switch to them using Ctrl+Alt+Fn or Alt+Left/Right key combinations.
""".format(StorageController.ROOT_MIN_SIZE / StorageController.GB)

    def __init__(self, app_ui: ApplicationUI):
        self._app_ui = app_ui
        _ok_btn = ok_btn('Close', on_press=self._close)
        super().__init__('Help', [urwid.Text(self.MSG),
                                  urwid.Text(''),
                                  button_pile([_ok_btn])], 0, 2)

    def _close(self, sender):
        self._app_ui.body.remove_overlay(self)
