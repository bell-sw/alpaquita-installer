#!/usr/bin/env python3

import os
import sys
import setuptools

setuptools.setup(
    name='alpaca_installer',
    version="1.0.0",
    description="Alpaca Installer",
    long_description="",
    author='BellSoft',
    author_email='info@bell-sw.com',
    url='https://bell-sw.com',
    license="AGPLv3+",
    packages=setuptools.find_packages(),
    scripts=[
          'bin/setup-alpaca',
        ],
    )
