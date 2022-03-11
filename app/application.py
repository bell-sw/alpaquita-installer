import asyncio

import urwid

from subiquitycore.ui.anchors import HeaderColumns
from subiquitycore.ui.utils import Color, LoadingDialog

from controllers.timezone import TimezoneController
from controllers.root_password import RootPasswordController
from controllers.proxy import ProxyController
from controllers.repo import RepoController
from controllers.user import UserController
from controllers.network import NetworkController
from controllers.installer import InstallerController
from .error import ErrorMsgStretchy
from nmanager.manager import NetworkManager

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
        self._header = urwid.Text('Header', align='center')
        self._title = urwid.Text('Title', align='left')
        title_cols = HeaderColumns([Color.frame_header_fringe(urwid.Text('')),
                                    Color.frame_header(self._title),
                                    Color.frame_header_fringe(urwid.Text('')),
                                    Color.frame_header_fringe(urwid.Text(''))])
        self._pile = urwid.Pile([('pack', self._header),
                                 ('pack', title_cols),
                                 ('pack', urwid.Text('')),
                                 urwid.ListBox([urwid.Text('Body')])
                                 ])
        self._pile.focus_position = 3

        super().__init__(Color.body(self._pile))

    def set_header(self, text):
        self._header.set_text(text)

    def set_title(self, title):
        self._title.set_text(title)

    def set_body(self, body):
        self._pile.contents[3] = (body, self._pile.contents[3][1])

    @property
    def body(self):
        return self._pile.contents[3][0]

    def keypress(self, size, key: str):
        if not self.block_input:
            return super().keypress(size, key)


class Application:
    make_ui = ApplicationUI

    def __init__(self, header: str, palette=()):
        # TODO: maybe move this into NetworkController
        self.nmanager = NetworkManager()
        self.nmanager.add_host_ifaces()

        self._controllers = []
        self._controllers.extend([
            NetworkController(self),
            UserController(self),
            TimezoneController(self),
            RootPasswordController(self),
            ProxyController(self),
            RepoController(self),
            InstallerController(self, create_config=True)
        ])
        self._ctrl_idx = 0

        self.ui = self.make_ui()
        self.ui.set_header(header)
        self._palette = palette

        self.aio_loop = asyncio.get_event_loop()
        self._urwid_loop = urwid.MainLoop(widget=self.ui, palette=self._palette,
                                          handle_mouse=False, pop_ups=True,
                                          event_loop=urwid.AsyncioEventLoop(loop=self.aio_loop))

    def controllers(self):
        return self._controllers

    def run(self):
        self._display_screen()
        self._urwid_loop.run()

    def _move_screen(self, increment):
        if increment > 0:
            self._ctrl_idx = min(self._ctrl_idx + 1, len(self._controllers) - 1)
        else:
            self._ctrl_idx = max(self._ctrl_idx - 1, 0)

        self._display_screen()

    def next_screen(self):
        self._move_screen(1)

    def prev_screen(self):
        self._move_screen(-1)

    def _display_screen(self):
        view = self._controllers[self._ctrl_idx].make_ui()
        self.ui.set_title(view.title)
        self.ui.set_body(view)

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
