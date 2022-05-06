#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import pytest

from alpaca_installer.installers.installer import InstallerException
from alpaca_installer.installers.secureboot import SecureBootInstaller
from .utils import new_installer


def create_installer(config: dict) -> SecureBootInstaller:
    return new_installer(SecureBootInstaller, config=config)


def test_no_install_shim_bootloader():
    create_installer({})


def test_invalid_install_shim_bootloader_type():
    with pytest.raises(InstallerException):
        create_installer({'install_shim_bootloader': ''})


def test_added_packages():
    installer = create_installer({'install_shim_bootloader': True})
    for pkg in ('sbsigntool', 'efitools', 'mokutil'):
        assert pkg in installer.packages
