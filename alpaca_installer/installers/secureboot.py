
#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

from .installer import Installer


class SecureBootInstaller(Installer):
    def __init__(self, target_root: str, config: dict, event_receiver):
        super().__init__(name='install_shim_bootloader', config=config,
                         event_receiver=event_receiver,
                         data_type=bool, target_root=target_root,
                         data_is_optional=True)

        if not self._data:
            return

        self.add_package('shim-signed', 'grub-efi-signed',
                         'sbsigntool', 'efitools', 'mokutil')

    def apply(self):
        pass
