#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

from alpaca_installer.common.utils import run_cmd
from .installer import Installer


class PackagesInstaller(Installer):
    def __init__(self, target_root: str, config: dict, event_receiver):
        super().__init__(name='extra_packages', config=config,
                         event_receiver=event_receiver,
                         target_root=target_root,
                         data_type=list,
                         data_is_optional=True)
        if self._data:
            for pkg in self._data:
                self.add_package(pkg)

        self.add_package('alpaca-base')

    def apply(self):
        self._event_receiver.start_event('Initializing APK database')
        self.apk_add(args=['--initdb'])

        self._event_receiver.start_event('Installing packages:')
        self.apk_add(args=self.packages)
