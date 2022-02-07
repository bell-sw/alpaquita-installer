import urwid

from subiquitycore.view import BaseView
from subiquitycore.ui.form import Form, PasswordField

class RootPasswordForm(Form):
    password = PasswordField('Password:')
    confirm = PasswordField('Confirm:')

    cancel_label = 'Back'

    def validate_password(self):
        if len(self.password.value) < 1:
            return 'Password is not set'

    # Since the confirm field is always the last one to be filled in,
    # having a validate_ method here allows us to validate the whole
    # form without a need to launching a pop up error window.
    def validate_confirm(self):
        if self.password.value != self.confirm.value:
            return 'Confirm and Passowrd fields do not match'


class RootPasswordView(BaseView):
    title = 'Root password'
    excerpt = 'Assign a password to the root account.'

    def __init__(self, controller, password: str):
        self._controller = controller

        self._form = RootPasswordForm()
        self._set_value(password)

        urwid.connect_signal(self._form, 'submit', self.done)
        urwid.connect_signal(self._form, 'cancel', self.cancel)

        super().__init__(self._form.as_screen(excerpt=self.excerpt,
                                              focus_buttons=False))

    def _set_value(self, password: str):
        self._form.password.widget.value = password
        self._form.confirm.widget.value = password

    def done(self, sender):
        self._controller.done(self._form.password.widget.value)

    def cancel(self, sender=None):
        self._controller.cancel()
