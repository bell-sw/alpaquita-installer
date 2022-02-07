from views.proxy import ProxyView

class ProxyController:
    def __init__(self, app):
        self._app = app
        self.proxy = ''

    def make_ui(self):
        return ProxyView(self, self.proxy)

    def done(self, proxy: str):
        self.proxy = proxy
        self._app.next_screen()

    def cancel(self):
        self._app.prev_screen()
