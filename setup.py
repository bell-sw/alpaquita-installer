#!/usr/bin/env python3

#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import setuptools

setuptools.setup(
    name='alpaquita_installer',
    version="0.5.4",
    description="Alpaquita Installer",
    long_description="",
    author='BellSoft',
    author_email='info@bell-sw.com',
    url='https://bell-sw.com',
    license="AGPLv3+",
    install_requires=['attrs', 'PyYAML', 'urwid'],
    packages=setuptools.find_packages(
        exclude=['subiquitycore.tests',
                 'subiquitycore.ui.tests',
                 'subiquitycore.ui.views.tests',
                 'tests']
    ),
    package_data={
        'alpaquita_installer': ['EULA', 'keys/**/*'],
    },
    scripts=[
          'bin/alpaquita-installer',
        ],
    )
