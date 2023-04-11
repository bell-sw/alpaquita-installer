#  SPDX-FileCopyrightText: 2023 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import os
from typing import Iterable, Optional

from alpaquita_installer.common.utils import run_cmd_live, write_file
from alpaquita_installer.common.events import EventReceiver


class APKManager:
    def __init__(self, event_receiver: EventReceiver):
        self._event_receiver = event_receiver

        self.keys_dir = '/etc/apk/keys'
        self.root_dir = None

    @staticmethod
    def _dir_exists(d: str):
        if not os.path.isdir(d):
            raise ValueError(f"'{d}' is not a directory")

    @staticmethod
    def _transform_apk_add(txt: str):
        if 'Installing' in txt:
            return ' * ' + txt.replace('Installing ', '')
        if txt.startswith('ERROR:'):
            return '   ' + txt
        return None

    @property
    def keys_dir(self) -> Optional[str]:
        return self._keys_dir

    @keys_dir.setter
    def keys_dir(self, val: Optional[str]):
        if val is not None:
            self._dir_exists(val)
        self._keys_dir = val

    @property
    def root_dir(self) -> Optional[str]:
        return self._root_dir

    @root_dir.setter
    def root_dir(self, val: Optional[str]):
        if val is not None:
            self._dir_exists(val)
        self._root_dir = val

    def write_repo_file(self, data):
        if self._root_dir is None:
            root_dir = '/'
        else:
            root_dir = self._root_dir
        apk_dir = os.path.join(root_dir, 'etc/apk')
        os.makedirs(apk_dir, exist_ok=True)
        repo_file = os.path.join(apk_dir, 'repositories')
        write_file(repo_file, 'w', data=data)

    def add(self, args: Iterable):
        all_args = ['apk', 'add', '--no-progress', '--update-cache', '--clean-protected']
        if self.root_dir is not None:
            all_args.extend(['--root', self.root_dir])
        if self.keys_dir is not None:
            all_args.extend(['--keys-dir', self.keys_dir])
        all_args.extend(args)
        run_cmd_live(args=all_args, event_receiver=self._event_receiver,
                     event_transform=self._transform_apk_add)
