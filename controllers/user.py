from typing import Optional

from attrs import define

from models.user import UserModel
from views.user import UserView, UserViewData

class UserController:
    def __init__(self, app):
        self._app = app
        self._model = None

    def make_ui(self):
        data = None
        if self._model is not None:
            data = UserViewData(full_name=self._model.full_name,
                                user_name=self._model.user_name,
                                is_admin=self._model.is_admin,
                                password=self._model.password)

        return UserView(self, data)

    def done(self, data: Optional[UserViewData]):
        # TODO add a try/except structure to catch possible
        # ValueError, TypeError errors from model validation
        new_model = None
        if data is not None:
           new_model = UserModel(full_name=data.full_name,
                                 user_name=data.user_name,
                                 is_admin=data.is_admin,
                                 password=data.password)

        self._model = new_model
        self._app.next_screen()

    def cancel(self):
        self._app.prev_screen()
