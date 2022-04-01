#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import re
from typing import Type, TypeVar

TV = TypeVar(name='TV')


def read_key_or_fail(data: dict, key: str, value_type: Type[TV]) -> TV:
    value = data.get(key, value_type())
    if not isinstance(value, value_type):
        raise ValueError("'{}' must be of type '{}'".format(key, str(value_type)))
    return value


def str_size_to_bytes(size: str) -> int:
    m = re.match(r'^([0-9]+)([KMG])?$', size)
    if not m:
        raise ValueError('Invalid size format: {}'.format(size))

    nbytes = int(m.group(1))
    suffixes = {'K': 1024,
                'M': 1024 * 1024,
                'G': 1024 * 1024 * 1024}
    suffix = m.group(2)
    if suffix:
        mult = suffixes.get(suffix, None)
        if not mult:
            raise ValueError("Invalid suffix '{}' in size {}".format(suffix, size))
        nbytes *= mult

    return nbytes
