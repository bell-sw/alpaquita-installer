from typing import Optional
import crypt
import logging

import yaml

from alpaca_installer.models.user import UserModel
from alpaca_installer.views.user import UserView, UserViewData
from .controller import Controller

log = logging.getLogger('controllers.users')


class UserController(Controller):
    def __init__(self, app):
        super().__init__(app)
        self._model = None

    def make_ui(self):
        data = None
        if self._model is not None:
            data = UserViewData(full_name=self._model.gecos,
                                user_name=self._model.name,
                                password=self._model.password)

        return UserView(self, data)

    def done(self, data: Optional[UserViewData]):
        # TODO add a try/except structure to catch possible
        # ValueError, TypeError errors from model validation
        new_model = None
        if data is not None:
           new_model = UserModel(gecos=data.full_name,
                                 name=data.user_name,
                                 is_admin=True,
                                 password=data.password)

        self._model = new_model
        self._app.next_screen()

    def cancel(self):
        self._app.prev_screen()

    def to_yaml(self) -> str:
        user_data = {'name': self._model.name,
                     'password': crypt.crypt(self._model.password),
                     'gecos': self._model.gecos,
                     'is_admin': self._model.is_admin}
        yaml_data = yaml.dump({'users': [user_data]})
        log.debug('export to yaml: {}'.format(yaml_data))
        return yaml_data
