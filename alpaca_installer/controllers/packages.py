#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import yaml
import os
import glob
import logging
from .controller import Controller
from .repo import RepoController
from alpaca_installer.views.packages import PackagesView

log = logging.getLogger('controllers.packages')

class PackagesController(Controller):
    def __init__(self, app):
        super().__init__(app)

        is_virt = len(glob.glob('/dev/disk/by-label/alpaca-virt-*')) > 0
        self._data = {'kernel': {'extramods': not is_virt},
                      'other': {'ssh_server': True}}

        log.debug(f'init: {self._data}')

    def make_ui(self):
        self._is_musl = self._app.controller('RepoController').get_libc_type() == 'musl'
        return PackagesView(self, self._data, self._is_musl)

    def done(self, data: dict):
        log.debug(f'done: {data}')

        self._data = data
        self._app.next_screen()

    def cancel(self):
        self._app.prev_screen()

    def _is_group_item(self, group: str, item: str):
        return self._data.get(group).get(item)

    def _add_pkg(self, pkgs, group, name, pkg_name):
        if (group not in self._data) or (name not in self._data.get(group)):
            return
        if self._is_group_item(group=group, item=name):
            pkgs.append(pkg_name)

    def to_yaml(self):
        epkgs = []
        enable_services = []

        self._add_pkg(epkgs, 'kernel', 'extramods', 'linux-lts-extra-modules')

        self._add_pkg(epkgs, 'jdk', 'jdk_8', 'liberica8')
        self._add_pkg(epkgs, 'jdk', 'jdk_11', 'liberica11')
        self._add_pkg(epkgs, 'jdk', 'jdk_17', 'liberica17')

        self._add_pkg(epkgs, 'nik', 'nik_21_11', 'liberica-nik-21-11')
        self._add_pkg(epkgs, 'nik', 'nik_21_17', 'liberica-nik-21-17')
        self._add_pkg(epkgs, 'nik', 'nik_22_11', 'liberica-nik-22-11')
        self._add_pkg(epkgs, 'nik', 'nik_22_17', 'liberica-nik-22-17')

        self._add_pkg(epkgs, 'libc', 'perf', 'musl-perf')

        self._add_pkg(epkgs, 'other', 'ssh_server', 'openssh-server')
        if self._is_group_item(group='other', item='ssh_server'):
            enable_services.append('sshd')

        data = {'extra_packages': epkgs}
        if enable_services:
            data['services'] = {'enabled': enable_services}

        return yaml.dump(data)
