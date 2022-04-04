#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import subprocess
import urllib
from typing import Optional

VALID_PROXY_URL_TEMPLATE = 'http://[[user][:password]@]hostname[:port]'


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


def validate_proxy_url(url: str):
    msg = "Proxy URL '{}' does not match template '{}'".format(
        url, VALID_PROXY_URL_TEMPLATE)

    pr = urllib.parse.urlparse(url)

    if (pr.scheme != 'http') or (not pr.hostname) or \
            any((pr.path, pr.params, pr.query, pr.fragment)) or \
            url.endswith(':'):
        raise ValueError(msg)

    try:
        _ = pr.port
    except ValueError:
        raise ValueError(msg) from None
