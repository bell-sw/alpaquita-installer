#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

from typing import Optional

import pytest

from alpaquita_installer.installers.installer import InstallerException
from alpaquita_installer.installers.bootloader import BootloaderInstaller
from .utils import new_installer


def create_installer(config: dict, efi_mount: Optional[str] = None) -> BootloaderInstaller:
    return new_installer(BootloaderInstaller, config=config, efi_mount=efi_mount)


def test_no_bootloader_device():
    with pytest.raises(ValueError, match="'bootloader_device'"):
        create_installer(config={})


def test_no_bootloader_device_with_efi():
    create_installer(config={}, efi_mount='/boot/efi')


def test_invalid_bootloader_device_type():
    with pytest.raises(InstallerException):
        create_installer(config={'bootloader_device': False})


def test_added_package_efi():
    installer = create_installer(config={'bootloader_device': '/dev/vda'},
                                 efi_mount='/boot/efi')
    for pkg in ('grub', 'grub-efi'):
        assert pkg in installer.packages


def test_added_package_non_efi():
    installer = create_installer(config={'bootloader_device': '/dev/vda'})
    for pkg in ('grub', 'grub-bios'):
        assert pkg in installer.packages
