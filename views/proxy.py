import urwid

from subiquitycore.view import BaseView
from subiquitycore.ui.form import Form, URLField

class ProxyForm(Form):
    cancel_label = 'Back'

    proxy_url = URLField('Proxy:')


class ProxyView(BaseView):
    title = 'Proxy'
    excerpt = ('If your system needs a HTTP proxy to connect to the Internet,'
              ' set it here.')

    def __init__(self, controller, proxy: str):
        self._controller = controller

        self._form = ProxyForm()
        self._form.proxy_url.widget.value = proxy

        urwid.connect_signal(self._form, 'submit', self.done)
        urwid.connect_signal(self._form, 'cancel', self.cancel)

        super().__init__(self._form.as_screen(excerpt=self.excerpt,
                                              focus_buttons=True))

    def done(self, sender):
        self._controller.done(self._form.proxy_url.widget.value)

    def cancel(self, sender=None):
        self._controller.cancel()
