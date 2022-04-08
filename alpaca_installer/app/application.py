#  SPDX-FileCopyrightText: 2020 Canonical, Ltd
#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import asyncio

import urwid
import sys
import getopt
import os
import logging

from subiquitycore.ui.utils import Color, LoadingDialog, Padding

from alpaca_installer.controllers.eula import EULAController
from alpaca_installer.controllers.timezone import TimezoneController
from alpaca_installer.controllers.proxy import ProxyController
from alpaca_installer.controllers.repo import RepoController
from alpaca_installer.controllers.user import UserController
from alpaca_installer.controllers.network import NetworkController
from alpaca_installer.controllers.storage import StorageController
from alpaca_installer.controllers.secureboot import SecureBootController
from alpaca_installer.controllers.packages import PackagesController
from alpaca_installer.controllers.installer import (
    InstallerController,
    ConsoleInstallerController,
)
from .error import ErrorMsgStretchy

# From Ubuntu
# When waiting for something of unknown duration, block the UI for at
# most this long before showing an indication of progress.
MAX_BLOCK_TIME = 0.1
# If an indication of progress is shown, show it for at least this
# long to avoid excessive flicker in the UI.
MIN_SHOW_PROGRESS_TIME = 1.0


class ApplicationUI(urwid.WidgetWrap):
    block_input = False

    def __init__(self):
        self._title = urwid.Text('Title', align='left')
        pile_items = [
            (1, Color.frame_header_fringe(urwid.SolidFill('\N{upper half block}'))),
            ('pack', Color.frame_header(Padding.center_79(self._title, min_width=76))),
            (1, Color.frame_header_fringe(urwid.SolidFill('\N{lower half block}'))),
            urwid.ListBox([urwid.Text('Body')])
        ]
        self._pile = urwid.Pile(pile_items)
        self._body_pos = len(pile_items) - 1
        self._pile.focus_position = self._body_pos

        super().__init__(Color.body(self._pile))

    def set_title(self, title):
        prefix = 'Alpaca Linux Installation'
        if title:
            text = '{} - {}'.format(prefix, title)
        else:
            text = prefix
        self._title.set_text(text)

    def set_body(self, body):
        self._pile.contents[self._body_pos] = (body, self._pile.contents[self._body_pos][1])

    @property
    def body(self):
        return self._pile.contents[self._body_pos][0]

    def keypress(self, size, key: str):
        if not self.block_input:
            return super().keypress(size, key)


class Application:
    make_ui = ApplicationUI

    def __init__(self, palette=()):

        self._no_ui = False

        try:
            opts, args = getopt.getopt(sys.argv[1:], 'hf:nd',
                                       ['help', 'config-file', 'no-ui', 'debug'])
        except getopt.GetoptError as err:
            print(f'Options parsing error: {err}')
            self.usage()
            sys.exit(1)

        self._config_file = ''
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                self.usage()
                sys.exit(0)
            elif opt in ("-f", "--config-file"):
                if not os.path.exists(arg):
                    print(f'Failed to find config file {arg}')
                    sys.exit(1)
                self._config_file = arg
            elif opt in ("-n", "--no-ui"):
                self._no_ui = True
            elif opt in ("-d", "--debug"):
                logging.basicConfig(filename='installer.log', filemode='w', level=logging.DEBUG)

        if self._no_ui and not self._config_file:
            self.usage()
            sys.exit(1)

        self._controllers = []

        if self._config_file:
            if self._no_ui:
                self._console_installer = ConsoleInstallerController(self, self._config_file)
                return
            self._controllers.append(InstallerController(self, False, self._config_file))
        else:
            self._controllers.extend([
                EULAController(self),
                NetworkController(self),
                ProxyController(self),
                RepoController(self),
                PackagesController(self),
                TimezoneController(self),
                UserController(self),
                StorageController(self),
                SecureBootController(self),
                InstallerController(self)
            ])

        self._type_to_controller = {}
        for c in self._controllers:
            self._type_to_controller[type(c).__name__] = c

        self._ctrl_idx = 0

        self.ui = self.make_ui()
        self._palette = palette

        self.aio_loop = asyncio.get_event_loop()
        self._urwid_loop = urwid.MainLoop(widget=self.ui, palette=self._palette,
                                          handle_mouse=False, pop_ups=True,
                                          event_loop=urwid.AsyncioEventLoop(loop=self.aio_loop))

    def usage(self):
        print(f'''Usage: alpaca-installer [OPTIONS]
        OPTIONS:
            -f --config-file x Get setup configuration from yaml file x
            -n --no-ui         Run the installation without a text-based UI. Requires config-file option
            -d --debug         Enable debug-level log
        ''')

    def is_efi(self) -> bool:
        return os.path.exists('/sys/firmware/efi')

    def controllers(self):
        return self._controllers

    def controller(self, type_name):
        return self._type_to_controller.get(type_name)

    def run(self):
        if self._no_ui:
            sys.exit(self._console_installer.run())

        if not self._display_screen():
            self.next_screen()
        self._urwid_loop.run()

    def _move_screen(self, increment):
        prev_idx = self._ctrl_idx

        if increment > 0:
            self._ctrl_idx = min(self._ctrl_idx + 1, len(self._controllers) - 1)
        else:
            self._ctrl_idx = max(self._ctrl_idx - 1, 0)

        if prev_idx == self._ctrl_idx:
            return

        if not self._display_screen():
            self._move_screen(increment)

    def next_screen(self):
        self._move_screen(1)

    def prev_screen(self):
        self._move_screen(-1)

    def _display_screen(self):
        view = self._controllers[self._ctrl_idx].make_ui()
        if view is None:
            return False

        self.ui.set_title(view.title)
        self.ui.set_body(view)
        return True

    def show_error_message(self, msg: str):
        self.ui.body.show_stretchy_overlay(ErrorMsgStretchy(self, msg))

    # From Ubuntu TuiApplication
    async def _wait_with_indication(self, awaitable, show, hide=None):
        """Wait for something but tell the user if it takes a while.

        When waiting for something that can take an unknown length of
        time, we want to tell the user if it takes more than a moment
        (defined as MAX_BLOCK_TIME) but make sure that we display any
        indication for long enough that the UI is not flickering
        incomprehensibly (MIN_SHOW_PROGRESS_TIME).
        """
        min_show_task = None

        def _show():
            self.ui.block_input = False
            nonlocal min_show_task
            min_show_task = self.aio_loop.create_task(
                asyncio.sleep(MIN_SHOW_PROGRESS_TIME))
            show()

        self.ui.block_input = True
        show_handle = self.aio_loop.call_later(MAX_BLOCK_TIME, _show)
        try:
            result = await awaitable
        finally:
            if min_show_task:
                await min_show_task
                if hide is not None:
                    hide()
            else:
                self.ui.block_input = False
                show_handle.cancel()

        return result

    # From Ubuntu TuiApplication
    async def wait_with_text_dialog(self, awaitable, message,
                                    *, can_cancel=False):
        ld = None

        task_to_cancel = None
        if can_cancel:
            if not isinstance(awaitable, asyncio.Task):
                orig = awaitable

                async def w():
                    return await orig

                awaitable = task_to_cancel = self.aio_loop.create_task(w())
            else:
                task_to_cancel = None

        def show_load():
            nonlocal ld
            ld = LoadingDialog(
                self.ui.body, self.aio_loop, message, task_to_cancel)
            self.ui.body.show_overlay(ld, width=ld.width)

        def hide_load():
            ld.close()

        return await self._wait_with_indication(
            awaitable, show_load, hide_load)

    def exit(self):
        self.aio_loop.stop()
