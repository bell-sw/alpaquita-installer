#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import os

from .installer import Installer
from typing import Optional


class BootloaderInstaller(Installer):
    def __init__(self, target_root: str, config: dict, event_receiver,
                 efi_mount: Optional[str]):
        yaml_key = 'bootloader_device'
        super().__init__(name=yaml_key, config=config,
                         event_receiver=event_receiver,
                         data_type=str, data_is_optional=True,
                         target_root=target_root)

        self._efi_mount = efi_mount
        if self._efi_mount:
            self.add_package('grub', 'grub-efi')
        else:
            if (not self._data) or (not isinstance(self._data, str)):
                raise ValueError("There must be an '{}' entry of type string".format(yaml_key))
            self.add_package('grub', 'grub-bios')

    def apply(self):
        pass

    def post_apply(self):
        self._event_receiver.start_event('Installing bootloader')
        self.run_in_chroot(args=['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])
        if self._efi_mount:
            self.run_in_chroot(args=['grub-install', '--target=x86_64-efi',
                                     '--efi-directory={}'.format(self._efi_mount),
                                     '--boot-directory=/boot', '--bootloader-id=alpaquita',
                                     '--no-nvram'])
            self.run_in_chroot(args=['install', '-D',
                                     os.path.join(self._efi_mount, 'EFI/alpaquita/grubx64.efi'),
                                     os.path.join(self._efi_mount, 'EFI/boot/bootx64.efi')])
        else:
            self.run_in_chroot(args=['grub-install', '--target=i386-pc',
                                     '--boot-directory=/boot', self._data])
