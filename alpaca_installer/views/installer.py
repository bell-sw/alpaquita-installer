#  SPDX-FileCopyrightText: 2015 Canonical, Ltd
#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import logging

from urwid import (
    LineBox,
    Text,
)
from subiquitycore.view import BaseView
from subiquitycore.ui.buttons import (
    cancel_btn,
    ok_btn,
    other_btn,
)
from subiquitycore.ui.container import Columns, ListBox, Pile
from subiquitycore.ui.form import Toggleable
from subiquitycore.ui.spinner import Spinner
from subiquitycore.ui.utils import button_pile, Padding
from subiquitycore.ui.width import widget_width

from alpaca_installer.common.types import ApplicationState

log = logging.getLogger('views.installer')


class MyLineBox(LineBox):
    def format_title(self, title):
        if title:
            return [" ", title, " "]
        else:
            return ""


class InstallerView(BaseView):

    title = 'Installation'

    def __init__(self, controller):
        self._controller = controller
        self.ongoing = {}  # context_id -> line containing a spinner

        self.reboot_btn = Toggleable(ok_btn(
            "Reboot Now", on_press=self.reboot))
        self.cancel_btn = cancel_btn(
            "Exit", on_press=self.cancel)
        self.view_log_btn = other_btn(
            "View full log", on_press=self.view_log)

        self.event_listbox = ListBox()
        self.event_linebox = MyLineBox(self.event_listbox)
        self.event_buttons = button_pile([self.view_log_btn])
        event_body = [
            ('weight', 1, Padding.center_79(self.event_linebox, min_width=76)),
            ('pack', Text("")),
            ('pack', self.event_buttons),
            ('pack', Text("")),
        ]
        self.event_pile = Pile(event_body)

        self.log_listbox = ListBox()
        log_linebox = MyLineBox(self.log_listbox, "Full installer output")
        log_body = [
            ('weight', 1, log_linebox),
            ('pack', button_pile([other_btn("Close",
                                  on_press=self.close_log)])),
            ]
        self.log_pile = Pile(log_body)

        super().__init__(self.event_pile)

    def _add_line(self, lb, line):
        lb = lb.base_widget
        walker = lb.body
        at_end = len(walker) == 0 or lb.focus_position == len(walker) - 1
        walker.append(line)
        if at_end:
            lb.set_focus(len(walker) - 1)
            lb.set_focus_valign('bottom')

    def event_start(self, context_id, context_parent_id, message):
        self.event_finish(context_parent_id)
        walker = self.event_listbox.base_widget.body
        spinner = Spinner(self._controller._app.aio_loop)
        spinner.start()
        new_line = Columns([
            ('pack', Text(message)),
            ('pack', spinner),
            ], dividechars=1)
        self.ongoing[context_id] = len(walker)
        self._add_line(self.event_listbox, new_line)

    def event_finish(self, context_id):
        index = self.ongoing.pop(context_id, None)
        if index is None:
            return
        walker = self.event_listbox.base_widget.body
        spinner = walker[index][1]
        spinner.stop()
        walker[index][0].set_text(walker[index][0].text + '.')
        walker[index] = walker[index][0]

    def finish_all(self):
        for context_id in list(self.ongoing):
            self.event_finish(context_id)

    def add_log_line(self, text):
        self._add_line(self.log_listbox, Text(text))

    def set_status(self, text):
        self.event_linebox.set_title(text)

    def _set_button_width(self):
        w = 14
        for b, o in self.event_buttons.original_widget.contents:
            w = max(widget_width(b), w)
        self.event_buttons.width = self.event_buttons.min_width = w

    def _set_buttons(self, buttons):
        p = self.event_buttons.original_widget
        p.contents[:] = [(b, p.options('pack')) for b in buttons]
        self._set_button_width()

    def update_for_state(self, state):
        if state == ApplicationState.DONE:
            self.title = "Install complete!"
            self.reboot_btn.base_widget.set_label("Reboot Now")
            btns = [
                self.view_log_btn,
                self.cancel_btn,
                self.reboot_btn,
                ]
        elif state == ApplicationState.ERROR:
            self.title = 'An error occurred during installation'
            self.reboot_btn.base_widget.set_label("Reboot Now")
            self.reboot_btn.enabled = True
            btns = [
                self.view_log_btn,
                self.cancel_btn,
                self.reboot_btn,
                ]
        else:
            raise Exception(state)
        self._controller._app.ui.set_header(self.title)
        self._set_buttons(btns)

    def reboot(self, btn):
        log.debug('reboot clicked')
        self.reboot_btn.base_widget.set_label("Rebooting...")
        self.reboot_btn.enabled = False
        self.event_buttons.original_widget._select_first_selectable()
        self._controller.click_reboot()
        self._set_button_width()

    def cancel(self, btn):
        self._controller.click_cancel()

    def view_log(self, btn):
        self._w = self.log_pile

    def close_log(self, btn):
        self._w = self.event_pile
