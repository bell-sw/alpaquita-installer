#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import urllib
import yaml
import logging
import os
from .controller import Controller
from alpaca_installer.views.repo import RepoView

log = logging.getLogger('controllers.repo')


class RepoController(Controller):
    def __init__(self, app):
        super().__init__(app)
        self._repo_base_url = 'https://packages.bell-sw.com'
        self._repos = []
        self._release = self.get_os_release().get('VERSION_ID', '').split('.')[0]
        self._release = self._release if self._release else 'stream'
        self._libc_type = 'musl' if os.path.exists('/lib/ld-musl-x86_64.so.1') else 'glibc'
        self._host_libc_type = self._libc_type

    def get_os_release(self):
        res = {}
        with open('/etc/os-release') as f:
            for line in f:
                k, v = line.rstrip().split('=')
                res[k] = v
        return res

    def get_libc_type(self) -> str:
        return self._libc_type

    def make_ui(self):
        return RepoView(self, self._repo_base_url, self._libc_type)

    def done(self, repo_base_url: str, libc_type: str):
        self._repo_base_url = repo_base_url
        self._libc_type = libc_type
        self._app.next_screen()

    def cancel(self):
        self._app.prev_screen()

    def get_repos(self, url, libc):
        self._repos = []
        for name in ['core', 'universe']:
            # TODO: fix the repo path before the release
            self._repos.append(urllib.parse.quote(
                                f'http://192.168.100.54/linux/linux_bellsoft/{name}',
#                               f'{url}/alpaca/{libc}/{self._release}/{name}',
                               safe='/:'))
        return self._repos

    def to_yaml(self):
        res = []

        if self._host_libc_type == self._libc_type:
            res.append('/media/disk/apks')
        res.extend(self._repos)

        yaml_data = yaml.dump({"repositories": res})

        log.debug(f"export to yaml: {yaml_data}")
        return yaml_data
