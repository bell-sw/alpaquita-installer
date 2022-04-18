#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import logging

import yaml

from alpaca_installer.views.proxy import ProxyView
from .controller import Controller

log = logging.getLogger('controllers.proxy')


class ProxyController(Controller):
    def __init__(self, app):
        super().__init__(app)
        self.proxy = ''

    def make_ui(self):
        return ProxyView(self, self.proxy)

    def done(self, proxy: str):
        self.proxy = proxy
        log.debug("Proxy: '{}'".format(self.proxy))
        self._app.next_screen()

    def cancel(self):
        self._app.prev_screen()

    def to_yaml(self) -> str:
        if not self.proxy:
            return ''

        yaml_data = yaml.dump({'proxy': self.proxy})
        log.debug(f"export to yaml: {yaml_data}")
        return yaml_data
