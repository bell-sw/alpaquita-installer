#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import re
import time
import subprocess

# TODO: add a type to input
def run_cmd(args, input=None, timeout: float = None, ignore_status: bool = False) -> subprocess.CompletedProcess:
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


def wait_iface_gets_ip(iface_name: str, ip_ver: int, timeout: float):
    if ip_ver == 4:
        inet_pattern = r'^\s*inet\s+'
    elif ip_ver == 6:
        inet_pattern = r'^\s*inet6\s+'
    else:
        raise ValueError(f'IP version is {ip_ver}, but only IPv4 and IPv6 are supported')

    sleep_interval = 1
    avail = timeout
    while avail > 0:
        args = ['ip', '-{}'.format(ip_ver), 'addr', 'show',
                'dev', iface_name, 'scope', 'global']
        res = run_cmd(args)
        stdout = res.stdout.decode('utf-8')
        for line in stdout.split('\n'):
            if re.match(inet_pattern, line):
                return

        time.sleep(sleep_interval)
        avail -= sleep_interval

    if avail <= 0:
        raise RuntimeError('Interface {} did not receive an IPv{} address in {} seconds'.format(
            iface_name, ip_ver, timeout
        ))


def get_active_iface_names() -> set[str]:
    res = set()
    try:
        with open('/run/ifstate', 'r') as file:
            for line in file.readlines():
                res.add(line.split('=')[0].strip())
    except FileNotFoundError:
        # TODO: log that /run/ifstate does not exist
        pass
    return res
