#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import os
import logging
import urllib

from .installer import Installer
from alpaquita_installer.common.utils import MEDIA_PATH, write_file
from .utils import read_key_or_fail, read_list

log = logging.getLogger('installer.repo')

#
# repositories:
#   keys: /dir/with/keys # optional
#   urls: [ url1, url2, .. ]
#


def validate_repo_url(url: str):
    msg = "'{}' is an invalid repository url".format(url)

    url = url.strip()
    if not url:
        raise ValueError(msg)

    pr = urllib.parse.urlparse(url)
    if pr.scheme:
        if (pr.scheme not in ('http', 'https')) or (not pr.hostname):
            raise ValueError(msg)


class RepoInstaller(Installer):
    APK_KEYS_DIR = '/etc/apk/keys'

    def __init__(self, target_root: str, config: dict, event_receiver):
        yaml_tag = 'repositories'
        super().__init__(name=yaml_tag, target_root=target_root,
                         event_receiver=event_receiver,
                         data_type=dict, config=config)
        self._repo_file = ''

        self._urls = read_list(self._data, 'urls', item_type=str,
                               error_label=f'{yaml_tag}/urls')
        if not self._urls:
            raise ValueError(f"'{yaml_tag}/urls' is empty")
        for url in self._urls:
            validate_repo_url(url)

        self._keys_dir = read_key_or_fail(self._data, 'keys', value_type=str,
                                          error_label=f'{yaml_tag}/keys')
        if not self._keys_dir:
            self._keys_dir = self.APK_KEYS_DIR
        if not os.path.isdir(self._keys_dir):
            raise ValueError(f"'{self._keys_dir}' is not a directory")

    def apply(self):
        self._event_receiver.start_event('Saving repositories')
        self._event_receiver.add_log_line(f'{self._urls}')

        apk_dir = self.abs_target_path('/etc/apk')
        os.makedirs(apk_dir, exist_ok=True)
        self._repo_file = os.path.join(apk_dir, 'repositories')
        self.create_repo_file()

        self._event_receiver.start_event('Initializing APK database:')
        self.apk_add(args=['--initdb', '--keys', self._keys_dir, 'alpaquita-keys'])

    def create_repo_file(self, media_disabled: bool = False):
        lines = []
        for r in self._urls:
            if media_disabled and r == MEDIA_PATH:
                r = '#' + r
            lines.append(r + '\n')
        write_file(self._repo_file, 'w', data=''.join(lines))

    def cleanup(self):
        self.create_repo_file(media_disabled=True)
