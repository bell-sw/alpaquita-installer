#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import os
from typing import Optional

import pytest

from alpaca_installer.common.events import EventReceiver
from alpaca_installer.common.utils import (
    run_cmd, run_cmd_live, write_file, button_width_for_label, validate_proxy_url)


def test_run_cmd_timeout():
    with pytest.raises(RuntimeError, match=r'(?i)did not complete'):
        run_cmd(args=['sleep', '1'], timeout=0.1)


def test_run_cmd_returncode():
    with pytest.raises(RuntimeError, match=r'(?i)exited with 1'):
        run_cmd(args=['false'])

    res = run_cmd(args=['false'], ignore_status=True)
    assert res.returncode == 1


def test_run_cmd_output():
    data = 'some_data'
    res = run_cmd(args=['cat'], input=bytes(data, encoding='utf-8'))
    assert data == res.stdout.decode()
    assert res.returncode == 0


def test_run_cmd_live_event_transform():
    def _transform(line: str) -> Optional[str]:
        if line.startswith('A'):
            return 'A'
        return None

    class Receiver(EventReceiver):
        event_prefix = 'Started event: '
        data = []

        def start_event(self, msg):
            self.data.append(f'{self.event_prefix}{msg}')

        def stop_event(self):
            pass

        def add_log_line(self, msg):
            self.data.append(msg)

    recv = Receiver()
    data = r'B\nA\n  \nC\n  A'
    res = run_cmd_live(args=['echo', '-e', '-n', data], event_receiver=recv,
                       event_transform=_transform)
    # Skip the first 'Running command ...' add_log_line
    assert recv.data[1:] == ['B', f'{recv.event_prefix}A', 'C', f'{recv.event_prefix}A']
    assert res.returncode == 0


def test_run_cmd_live_output_returncode():
    with pytest.raises(RuntimeError, match=r'(?i)exited with 1'):
        run_cmd_live(args=['false'])

    res = run_cmd_live(args=['false'], ignore_status=True)
    assert res.returncode == 1


def test_write_file(tmp_path):
    file_path = os.path.join(tmp_path, 'temp_file')
    data = 'some data'
    bdata = bytes(data, encoding='utf-8')

    write_file(path=file_path, mode='w', data=data)
    with open(file_path, 'r') as file:
        assert data == file.read()

    write_file(path=file_path, mode='a', data=data)
    with open(file_path, 'r') as file:
        assert data + data == file.read()

    write_file(path=file_path, mode='wb', data=bdata)
    with open(file_path, 'rb') as file:
        assert bdata == file.read()

    with pytest.raises(ValueError, match=r'(?i)unsupported mode'):
        write_file(path=file_path, mode='invalid mode', data=data)


def test_validate_proxy_url():
    invalid_urls = ['ftp://domain.com:80',
                    'https://domain.com:80',
                    'http://domain.com:invalid_port',
                    'http://domain.com:80/path',
                    'http://domain.com/path',
                    'http://domain.com/path/',
                    'http://domain.com:port',
                    'http://domain.com?arg=val',
                    'http://',
                    'domain.com:80',
                    'domain.com',
                    ]

    for url in invalid_urls:
        with pytest.raises(ValueError, match=r'(?i)does not match template'):
            validate_proxy_url(url)


def test_button_width_for_label():
    label = 'some label'
    assert len(f'[ {label} ]') == button_width_for_label(label)
