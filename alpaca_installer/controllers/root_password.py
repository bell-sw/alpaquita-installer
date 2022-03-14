from alpaca_installer.views.root_password import RootPasswordView

class RootPasswordController:
    def __init__(self, app):
        self._app = app
        self.password = ''

    def make_ui(self):
        return RootPasswordView(self, self.password)

    def done(self, password: str):
        self.password = password
        self._app.next_screen()

    def cancel(self):
        self._app.prev_screen()
