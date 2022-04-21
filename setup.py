#!/usr/bin/env python3

#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import setuptools

setuptools.setup(
    name='alpaca_installer',
    version="0.3.0",
    description="Alpaca Installer",
    long_description="",
    author='BellSoft',
    author_email='info@bell-sw.com',
    url='https://bell-sw.com',
    license="AGPLv3+",
    packages=setuptools.find_packages(),
    package_data={
        'alpaca_installer': ['EULA'],
    },
    scripts=[
          'bin/alpaca-installer',
        ],
    )
