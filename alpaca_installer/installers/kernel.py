#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import os
import re

from .installer import Installer
from .utils import read_list

# Optional
#
# kernel:
#   cmdline: [ 'quiet' ]
#


class KernelInstaller(Installer):
    def __init__(self, target_root: str, config: dict, event_receiver):
        yaml_tag = 'kernel'
        super().__init__(name=yaml_tag, config=config,
                         event_receiver=event_receiver,
                         data_type=dict, data_is_optional=True,
                         target_root=target_root)

        self._cmdline: list[str] = []
        if self._data is not None:
            yaml_key = 'cmdline'
            self._cmdline = read_list(self._data, key=yaml_key, item_type=str,
                                      error_label=f'{yaml_tag}/{yaml_key}')
        else:
            self._cmdline = ['quiet']

        self.add_package('linux-lts')

    def apply(self):
        pass

    def post_apply(self):
        self._event_receiver.start_event('Regenerating initrd')

        kver = None
        for name in os.listdir(self.abs_target_path('/boot')):
            m = re.match(r'^config-(\d+.*)$', name)
            if m:
                kver = m.group(1)
                break
        if not kver:
            raise RuntimeError('Unable to determine the installed kernel version')
        self.run_in_chroot(args=['dracut', '-f', '/boot/initramfs-lts', kver])

        data = """
GRUB_TIMEOUT=2
GRUB_DISABLE_SUBMENU=y
GRUB_DISABLE_RECOVERY=true
GRUB_CMDLINE_LINUX_DEFAULT="{}"
""".format(' '.join(self._cmdline))
        with open(self.abs_target_path('/etc/default/grub'), 'w') as file:
            file.write(data)
