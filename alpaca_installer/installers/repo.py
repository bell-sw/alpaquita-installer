#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import os
import logging

from .installer import Installer

log = logging.getLogger('installer.repo')


class RepoInstaller(Installer):
    def __init__(self, target_root: str, config: dict, event_receiver):
        super().__init__(name='repositories', target_root=target_root,
                         event_receiver=event_receiver,
                         data_type=list, config=config)

    def apply(self):
        self._event_receiver.start_event('Saving repositories')
        self._event_receiver.add_log_line(f'{self._data}')

        apk_dir = self.abs_target_path('/etc/apk')
        os.makedirs(apk_dir, exist_ok=True)
        repo_file = os.path.join(apk_dir, 'repositories')
        with open(repo_file, 'a') as apk_repo_file:
            for r in self._data:
                apk_repo_file.write('\n' + r)
            apk_repo_file.write('\n')
