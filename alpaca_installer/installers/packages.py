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

        self.add_package('acct', 'alpaca-base')

    def apply(self):
        self._event_receiver.start_event('Initializing APK database')

        common = ['apk', 'add', '--root', self.target_root,
                  '--keys', '/etc/apk/keys',  # install using keys from the host system
                  '--no-progress']

        run_cmd(args=(common + ['--initdb']), event_receiver=self._event_receiver)

        args = common + ['--update-cache', '--clean-protected']
        args.extend(self.packages)

        self._event_receiver.start_event(f'Installing packages: {sorted(self.packages)}')
        run_cmd(args=args, event_receiver=self._event_receiver)
