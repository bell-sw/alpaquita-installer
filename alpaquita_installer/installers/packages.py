#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

from alpaquita_installer.common.utils import run_cmd
from .installer import Installer
from .utils import read_list

# Optional
#
# extra_packages: [ 'pkg1', 'pkg2' ]
#


class PackagesInstaller(Installer):
    def __init__(self, target_root: str, config: dict, event_receiver):
        yaml_tag = 'extra_packages'
        super().__init__(name=yaml_tag, config=config,
                         event_receiver=event_receiver,
                         target_root=target_root,
                         data_type=list,
                         data_is_optional=True)
        if self._data:
            extra_pkgs = read_list(config, key=yaml_tag, item_type=str,
                                   error_label=yaml_tag)
            for pkg in extra_pkgs:
                self.add_package(pkg)

        self.add_package('distro-base')

    def apply(self):
        self._event_receiver.start_event('Installing packages:')
        self.apk_add(args=self.packages)
