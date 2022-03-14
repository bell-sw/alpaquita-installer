import urwid

from subiquitycore.view import BaseView
from subiquitycore.ui.form import (
    Form,
    ReadOnlyField
)

class InstallerForm(Form):
    cancel_label = 'Back'

class InstallerView(BaseView):
    title = 'Installation'

    def __init__(self, controller):
        self._controller = controller

        self._form = InstallerForm()
        urwid.connect_signal(self._form, 'submit', self.done)
        urwid.connect_signal(self._form, 'cancel', self.cancel)

        super().__init__(self._form.as_screen(excerpt='', focus_buttons=True))

    def done(self, sender):
        self._controller.done()

    def cancel(self, sender=None):
        self._controller.cancel()
