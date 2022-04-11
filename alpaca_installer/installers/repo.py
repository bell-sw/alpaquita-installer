#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import os
import logging

from .installer import Installer
from alpaca_installer.common.utils import run_cmd, MEDIA_PATH

log = logging.getLogger('installer.repo')


class RepoInstaller(Installer):
    def __init__(self, target_root: str, config: dict, event_receiver):
        super().__init__(name='repositories', target_root=target_root,
                         event_receiver=event_receiver,
                         data_type=list, config=config)
        self._repo_file = ''

    def apply(self):
        self._event_receiver.start_event('Saving repositories')
        self._event_receiver.add_log_line(f'{self._data}')

        apk_dir = self.abs_target_path('/etc/apk')
        os.makedirs(apk_dir, exist_ok=True)
        self._repo_file = os.path.join(apk_dir, 'repositories')
        self.create_repo_file()

    def create_repo_file(self, media_disabled: bool = False):
        with open(self._repo_file, 'w') as apk_repo_file:
            for r in self._data:
                if media_disabled and r == MEDIA_PATH:
                    r = '#' + r
                apk_repo_file.write(r + '\n')

    def cleanup(self):
        self.create_repo_file(media_disabled=True)

        cd_dev = '/dev/cdrom'
        if os.path.exists(cd_dev):
            run_cmd(args=['eject', cd_dev])
