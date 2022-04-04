#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import asyncio
import yaml
import logging
import urwid
import time
import abc

from subiquitycore.async_helpers import run_in_thread
from alpaca_installer.views.installer import InstallerView
from alpaca_installer.installers.storage import StorageInstaller
from alpaca_installer.installers.repo import RepoInstaller
from alpaca_installer.installers.proxy import ProxyInstaller
from alpaca_installer.installers.packages import PackagesInstaller
from alpaca_installer.installers.services import ServicesInstaller
from alpaca_installer.installers.swapfile import SwapfileInstaller
from alpaca_installer.installers.timezone import TimezoneInstaller
from alpaca_installer.installers.users import UsersInstaller
from alpaca_installer.installers.network import NetworkInstaller
from alpaca_installer.installers.kernel import KernelInstaller
from alpaca_installer.installers.secureboot import SecureBootInstaller
from alpaca_installer.installers.bootloader import BootloaderInstaller
from alpaca_installer.installers.installer import (
    InstallerException,
    EventReceiver
)
from .controller import Controller

from alpaca_installer.common.utils import run_cmd
from alpaca_installer.common.types import ApplicationState

log = logging.getLogger('controllers.installer')

class BaseInstallerController(Controller, EventReceiver):
    def __init__(self, app, create_config, config_file):
        super().__init__(app)
        self._config_file = config_file
        self._create_config = create_config

    @abc.abstractmethod
    def _print_log_line(self, msg):
        pass

    def _run(self):
        try:
            if self._create_config:
                self.create_config()
            self._install_config()
        except IOError as err:
            raise InstallerException(f'Failed to open/read {self._config_file} file: {err}')
        except yaml.YAMLError as err:
            raise InstallerException(f'An error occured while parsing {self._config_file} file: {err}')
        except Exception as err:
            raise InstallerException(f'An error occured: {err}')

    def _add_log_line(self, msg):
        msgs = msg.split("\\n")
        for m in msgs:
            if m:
                self._print_log_line(m)

    def _install_config(self):
        self.start_event(f'Reading config {self._config_file} file')

        with open(self._config_file) as f:
            config_str = f.read()

        if not config_str:
            raise InstallerException(f'Config is empty')

        config = yaml.safe_load(config_str)
        target_root = '/mnt/target_root'
        self.add_log_line(f'Using new root {target_root}')
        storage_installer = StorageInstaller(target_root=target_root,
                                             config=config, event_receiver=self)
        efi_mount = storage_installer.efi_mount_point
        pkgs_installer = PackagesInstaller(target_root=target_root,
                                           config=config, event_receiver=self)

        installers = [
            storage_installer,
            RepoInstaller(target_root=target_root, config=config, event_receiver=self),
            ProxyInstaller(target_root=target_root, config=config, event_receiver=self),
            pkgs_installer,
            ServicesInstaller(target_root=target_root, config=config, event_receiver=self),
            SwapfileInstaller(target_root=target_root, config=config, event_receiver=self),
            TimezoneInstaller(target_root=target_root, config=config, event_receiver=self),
            UsersInstaller(target_root=target_root, config=config, event_receiver=self),
            NetworkInstaller(target_root=target_root, config=config, event_receiver=self),
            KernelInstaller(target_root=target_root, config=config, event_receiver=self),
            SecureBootInstaller(target_root=target_root, config=config, event_receiver=self),
            BootloaderInstaller(target_root=target_root, config=config, event_receiver=self,
                                efi_mount=efi_mount),
        ]

        for i in installers:
            pkgs_installer.add_package(*i.packages)

        for i in installers:
            i.apply()

        for i in installers:
            i.post_apply()

        for i in reversed(installers):
            i.cleanup()


class ConsoleInstallerController(BaseInstallerController):
    def __init__(self, app, config_file):
        super().__init__(app, False, config_file)

    def run(self):
        try:
            self._run()
        except Exception as err:
            print(f'{err}')
            return 1
        return 0

    def start_event(self, msg):
        print(msg)

    def stop_event(self):
        pass

    def add_log_line(self, msg):
        self._add_log_line(msg)

    def _print_log_line(self, msg):
        print(msg)

class InstallerController(BaseInstallerController):
    def __init__(self, app, create_config=True, config_file='setup.yaml'):
        super().__init__(app, create_config, config_file)
        self._view = InstallerView(self)
        self._eloop = asyncio.get_event_loop()

    def create_config(self):
        self.start_event(f'Creating config {self._config_file} file')
        with open(self._config_file, 'w') as f:
            for c in self._app.controllers():
                yaml_str = c.to_yaml();
                if yaml_str:
                    f.write(yaml_str + '\n')

    async def _start(self):
        try:
            await run_in_thread(self._run)
        except Exception as err:
            self._event_start(f'{err}')
            self._event_finish()
            self._view.update_for_state(ApplicationState.ERROR)
            return

        self._event_finish()
        self._view.update_for_state(ApplicationState.DONE)

    def add_log_line(self, msg):
        self._eloop.call_soon_threadsafe(self._add_log_line, msg)
    def start_event(self, msg):
        self._eloop.call_soon_threadsafe(self._event_start, msg)
    def stop_event(self):
        self._eloop.call_soon_threadsafe(self._event_finish)

    def _event_start(self, msg):
        self._view.add_log_line(msg)
        self._event_finish()
        self._view.event_start('', '', msg)

    def _event_finish(self):
        self._view.event_finish('')

    def _print_log_line(self, msg):
        self._view.add_log_line(msg)

    def click_cancel(self):
        self._app.exit()

    def click_reboot(self):
        run_cmd(args=['/sbin/reboot'])

    def make_ui(self):
        self._event_start('Starting installation')
        self._app.aio_loop.create_task(self._start())
        return self._view
