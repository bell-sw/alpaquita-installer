import asyncio

import urwid

from subiquitycore.ui.anchors import HeaderColumns
from subiquitycore.ui.utils import Color

from controllers.timezone import TimezoneController
from controllers.root_password import RootPasswordController
from controllers.proxy import ProxyController
from controllers.user import UserController
from .error import ErrorMsgStretchy

class ApplicationUI(urwid.WidgetWrap):
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


class Application:
    make_ui = ApplicationUI

    def __init__(self, header: str, palette=()):
        self._controllers = []
        self._controllers.extend([
            UserController(self),
            TimezoneController(self),
            RootPasswordController(self),
            ProxyController(self),
        ])
        self._ctrl_idx = 0

        self.ui = self.make_ui()
        self.ui.set_header(header)
        self._palette = palette

        self.aio_loop = asyncio.get_event_loop()
        self._urwid_loop = urwid.MainLoop(widget=self.ui, palette=self._palette,
                                          handle_mouse=False, pop_ups=True,
                                          event_loop=urwid.AsyncioEventLoop(loop=self.aio_loop))

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
