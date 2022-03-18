from typing import Optional


from alpaca_installer.models.user import UserModel
from alpaca_installer.views.user import UserView, UserViewData


class UserController:
    def __init__(self, app):
        self._app = app
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
