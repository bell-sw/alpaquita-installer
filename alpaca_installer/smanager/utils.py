#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import os
import time
import subprocess
from typing import Optional


def run_cmd(args, input: Optional[bytes] = None, timeout: float = None, ignore_status: bool = False) -> subprocess.CompletedProcess:
    try:
        res = subprocess.run(args, input=input,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        raise RuntimeError("'{}' did not complete in {} seconds".format(
            ' '.join(args), timeout
        )) from None

    if (not ignore_status) and (res.returncode != 0):
        raise RuntimeError("'{}' exited with {}: {}".format(
            ' '.join(args), res.returncode, res.stderr
        ))
    return res


def get_block_device_size(device_path: str) -> int:
    res = run_cmd(['blockdev', '--getsize64', device_path])
    return int(res.stdout.decode())


def get_block_device_uuid(device_path: str) -> str:
    # blkid from busybox does not report UUID for vfat...
    res = run_cmd(['lsblk', '-n', '-o', 'UUID', device_path])
    uuid = res.stdout.decode().strip()
    if not uuid:
        raise RuntimeError('Unable to determine a file system UUID of {}'.format(device_path))
    return uuid


def wait_path_created(path: str, timeout=10.0):
    spent_time = 0.0
    sleep_interval = 0.1
    created = False

    while spent_time < timeout:
        if os.path.exists(path):
            created = True
            break

        time.sleep(sleep_interval)
        spent_time += sleep_interval

    if not created:
        raise RuntimeError('{}: not created in {} seconds'.format(
            path, timeout))
