#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import os
import re

from alpaquita_installer.common.utils import write_file
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
        self.run_in_chroot(args=['dracut', '-f', f'/boot/initramfs-{kver}', kver])

        data = """\
GRUB_TIMEOUT=0
GRUB_TIMEOUT_STYLE=hidden
GRUB_DISABLE_SUBMENU=y
GRUB_DISABLE_RECOVERY=true
GRUB_CMDLINE_LINUX_DEFAULT="{}"
GRUB_DEFAULT=saved

# Note that Alpaquita doesn't have os-prober installed by default,
# therefore /etc/grub.d/30_os-prober is no-op. In order to use it,
# you need to install the os-prober package.
GRUB_DISABLE_OS_PROBER=false
""".format(' '.join(self._cmdline))
        write_file(self.abs_target_path('/etc/default/grub'), 'w', data=data)
