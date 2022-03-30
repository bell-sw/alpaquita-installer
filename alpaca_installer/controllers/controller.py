from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from alpaca_installer.app.application import Application


class Controller:
    def __init__(self, app: Application):
        self._app = app

    def to_yaml(self) -> str:
        return ''
