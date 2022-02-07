import re
from typing import Optional

import logging

from attrs import define
import urwid

from subiquitycore.view import BaseView
from subiquitycore.ui.form import (
    Form,
    SubForm,
    SubFormField,
    StringField,
    PasswordField,
    BooleanField,
)

from models.user import USERNAME_REGEX, USERNAME_MAX_LEN

@define
class UserViewData:
    full_name: str
    user_name: str
    is_admin: bool
    password: str


class UserCreationForm(SubForm):
    full_name = StringField('Full name:')
    user_name = StringField('User name:')
    is_admin = BooleanField('Make this user administrator')

    password = PasswordField('Password:')
    confirm = PasswordField('Confirm:')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate_user_name(self):
        user_name = self.user_name.value

        if len(user_name) < 1:
            return 'User name is not set'
        if len(user_name) > USERNAME_MAX_LEN:
            return f'User name must be <= {USERNAME_MAX_LEN} characters'
        if not re.match(USERNAME_REGEX, user_name):
            return f"User name must match regex '{USERNAME_REGEX}'"

    def validate_password(self):
        if len(self.password.value) < 1:
            return 'Password is not set'

    def validate_confirm(self):
        if self.password.value != self.confirm.value:
            return 'Confirm and Password fields do not match'



class UserForm(Form):
    cancel_label = 'Back'

    create_user = BooleanField('Create a user')
    creation_form = SubFormField(UserCreationForm, '')

    def __init__(self, data: Optional[UserViewData]):
        super().__init__()
        urwid.connect_signal(self.create_user.widget, 'change', self._toggle)

        logging.warn(dir(self.creation_form))
        logging.warn(dir(self.creation_form.form))

        if data is not None:
            form_data = {}
            form_data['full_name'] = data.full_name
            form_data['user_name'] = data.user_name
            form_data['is_admin'] = data.is_admin
            form_data['password'] = data.password
            form_data['confirm'] = data.password
            self.creation_form.value = form_data
            self.create_user.value = True

        self._toggle(None, self.create_user.value)

    def _toggle(self, sender, value):
        self.creation_form.enabled = value
        if not self.creation_form.enabled:
            # Even when the subform contains invalid data, we ignore it
            self.creation_form.in_error = False
            self.validated()

    def validate_creation_form(self):
        subform = self.creation_form.widget.form
        if any((field.in_error for field in subform._fields)):
            # An empty string saves us from deleting the field error
            # message, when create_user.enabled goes from False to True.
            # Anyway, any validation errors will be shown next to
            # corresponding fields in the creation_form subform fields.
            return ''

class UserView(BaseView):
    title = 'Create user'
    excerpt = "It's recommended to create a non-root user account."

    def __init__(self, controller, data: Optional[UserViewData]):
        logging.basicConfig(filename='/tmp/log')


        self._controller = controller

        self._form = UserForm(data)

        urwid.connect_signal(self._form, 'submit', self.done)
        urwid.connect_signal(self._form, 'cancel', self.cancel)

        super().__init__(self._form.as_screen(excerpt=self.excerpt,
                                              focus_buttons=False))

    def done(self, sender):
        data = None
        if self._form.create_user.value:
            form_data = self._form.creation_form.value
            data = UserViewData(full_name=form_data['full_name'],
                                user_name=form_data['user_name'],
                                is_admin=form_data['is_admin'],
                                password=form_data['password'])

        self._controller.done(data)

    def cancel(self, sender=None):
        self._controller.cancel()
