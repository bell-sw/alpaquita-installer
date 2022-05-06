#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import pytest

from alpaca_installer.installers.installer import InstallerException
from alpaca_installer.installers.users import UsersInstaller
from .utils import new_installer


def create_installer(config: dict) -> UsersInstaller:
    return new_installer(UsersInstaller, config=config)


def test_no_users():
    with pytest.raises(InstallerException):
        create_installer({})


def test_users_invalid_type():
    with pytest.raises(InstallerException):
        create_installer({'users': False})

    with pytest.raises(ValueError):
        create_installer({'users': [{'name': 'user1', 'password': 'password_hash', 'is_admin': False},
                                    False]})


def test_no_admin_user():
    with pytest.raises(InstallerException, match=r'(?i)admin user'):
        create_installer({'users': [{'name': 'user', 'password': 'password_hash'}]})


def test_invalid_user():
    users = [{'name': 'user name', 'password': 'password_hash'},
             {'name': 'user'},
             {'password': 'password_hash'},
             {'name': 'user', 'password': 'password_with_:'},
             {'name': 'user', 'password': 'password with spaces'},
             {'name': False},
             {'name': 'user', 'password': False},
             {'name': 'user', 'password': 'password_hash', 'gecos': False},
             {'name': 'user', 'password': 'password_hash', 'gecos': 'gecos_value',
              'is_admin': 'is_admin_value'}
             ]

    for invalid_user in users:
        with pytest.raises(InstallerException):
            create_installer({'users': [invalid_user]})


def test_admin_user():
    installer = create_installer({'users': [{'name': 'user', 'password': 'password_hash',
                                             'is_admin': True}]})
    assert 'sudo' in installer.packages
