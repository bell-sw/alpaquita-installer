#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import os

import pytest

from alpaquita_installer.installers.installer import InstallerException
from alpaquita_installer.installers.repo import RepoInstaller
from .utils import new_installer


def create_installer(config: dict) -> RepoInstaller:
    return new_installer(RepoInstaller, config=config)


def test_no_repositories():
    with pytest.raises(InstallerException):
        create_installer({})


def test_invalid_urls():
    for urls in ([], ['http://domain.com', False], False):
        with pytest.raises(ValueError, match="'repositories/urls'"):
            create_installer({'repositories': {'urls': urls}})

    invalid_urls = [' ', '', 'http://', 'ftp://domain.com', 'https://']
    for url in invalid_urls:
        with pytest.raises(ValueError, match=r'(?i)invalid repository'):
            create_installer({'repositories': {'urls': [url]}})


def test_invalid_keys_type():
    with pytest.raises(ValueError):
        create_installer({'repositories': {'urls': ['http://domain.com'],
                                           'keys': False}})


def test_non_existent_keys_dir(tmp_path):
    config = {'repositories': {
        'urls': ['http://domain.com'],
        'keys': os.path.join(tmp_path, 'nonexistent')
    }}
    with pytest.raises(ValueError, match=r'(?i)is not a directory'):
        create_installer(config)


def test_valid_config(tmp_path):
    create_installer({'repositories': {
        'keys': str(tmp_path),
        'urls': ['http://domain.com', 'https://domain2.com/path', '/path/to/apks']
    }})
