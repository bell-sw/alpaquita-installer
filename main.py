import urwid

from subiquitycore.ui.anchors import HeaderColumns

from subiquitycore.ui.utils import Color

from controllers.timezone import TimezoneController
from controllers.root_password import RootPasswordController
from controllers.proxy import ProxyController
from controllers.user import UserController

PALETTE = [
#    ('frame_header_fringe', 'white',   'black'),
    ('frame_header_fringe', 'black',   'light cyan'),
#    ('frame_header',        'black',   'white'),
    ('frame_header',        'black', 'light cyan'),
    ('body',                'white',   'black'),

    ('done_button',         'white',   'black'),
    ('danger_button',       'white',   'black'),
    ('other_button',        'white',   'black'),
    ('done_button focus',   'black',   'light cyan'),
    ('danger_button focus', 'black',   'light cyan'),
    ('other_button focus',  'black',   'light cyan'),

    ('menu_button',         'white',   'black'),
    ('menu_button focus',   'black',   'light cyan'),
    ('frame_button',        'black',   'white'),
    ('frame_button focus',  'white',   'black'),

    ('info_primary',        'white',   'black'),
    ('info_minor',          'dark gray',   'black'),
    ('info_minor header',   'dark gray',   'black'),
    ('info_error',          'light red',   'black'),

    ('string_input',        'dark gray',   'white'),
    ('string_input focus',  'black',   'light cyan'),

    ('progress_incomplete', 'white',   'black'),
    ('progress_complete',   'black',   'white'),
    ('scrollbar',           'light cyan',   'black'),
    ('scrollbar focus',     'light cyan',   'black'),
#    ('scrollbar_fg',        'white',   'dark gray'),
#    ('scrollbar_bg',        'white',   'dark gray'),
]

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
                                 urwid.ListBox([urwid.Text('Body')])
                                 ])
        self._pile.focus_position = 2

        super().__init__(Color.body(self._pile))

    def set_header(self, text):
        self._header.set_text(text)

    def set_title(self, title):
        self._title.set_text(title)

    def set_body(self, body):
        self._pile.contents[2] = (body, self._pile.contents[2][1])

class Application:
    make_ui = ApplicationUI

    def __init__(self):
        self._controllers = []
        self._controllers.extend([
            UserController(self),
            TimezoneController(self),
            RootPasswordController(self),
            ProxyController(self),
        ])
        self._ctrl_idx = 0

        self.ui = self.make_ui()
        self.ui.set_header('Alpaca Linux Installation')

        self._display_screen()

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

app = Application()
urwid.MainLoop(app.ui, PALETTE, pop_ups=True).run()
