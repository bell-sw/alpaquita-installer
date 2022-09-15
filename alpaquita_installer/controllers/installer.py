#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

from __future__ import annotations
import asyncio
import yaml
import logging
import abc
import os
import shutil
import stat
from typing import TYPE_CHECKING

from subiquitycore.async_helpers import run_in_thread
from alpaquita_installer.views.installer import InstallerView
from alpaquita_installer.installers.storage import StorageInstaller
from alpaquita_installer.installers.repo import RepoInstaller
from alpaquita_installer.installers.proxy import ProxyInstaller
from alpaquita_installer.installers.packages import PackagesInstaller
from alpaquita_installer.installers.services import ServicesInstaller
from alpaquita_installer.installers.swapfile import SwapfileInstaller
from alpaquita_installer.installers.timezone import TimezoneInstaller
from alpaquita_installer.installers.users import UsersInstaller
from alpaquita_installer.installers.network import NetworkInstaller
from alpaquita_installer.installers.kernel import KernelInstaller
from alpaquita_installer.installers.secureboot import SecureBootInstaller
from alpaquita_installer.installers.bootloader import BootloaderInstaller
from alpaquita_installer.installers.installer import InstallerException
from alpaquita_installer.common.events import EventReceiver
from alpaquita_installer.common.utils import DEFAULT_CONFIG_FILE
from .controller import Controller

if TYPE_CHECKING:
    from alpaquita_installer.app.application import Application

log = logging.getLogger('controllers.installer')


def err_msg_with_debug_log_file(err_msg: str, app: Application):
    if app.debug_log_file:
        return f"{err_msg}\nAdditional debug information is available in '{app.debug_log_file}'."
    else:
        return err_msg


class BaseInstallerController(Controller, EventReceiver):
    TARGET_ROOT = '/mnt/target_root'

    def __init__(self, app: Application, create_config, config_file):
        super().__init__(app)
        self._config_file = config_file
        self._create_config = create_config

    def _run(self):
        try:
            if self._create_config:
                self.create_config()
            self._install_config()
        except yaml.YAMLError as err:
            raise InstallerException(f'An error occured while parsing {self._config_file} file: {err}')
        except Exception as err:
            raise InstallerException(f'An error occured: {err}')

    def _copy_yaml_config(self):
        copied_config_rel = os.path.join('/root', os.path.basename(DEFAULT_CONFIG_FILE))
        self.start_event((f"Saving the config file for this installation to "
                          f"'{copied_config_rel}' on the new system."))
        copied_config_abs = os.path.join(self.TARGET_ROOT, copied_config_rel.lstrip('/'))
        shutil.copy(self._config_file, copied_config_abs)
        os.chown(copied_config_abs, 0, 0)
        os.chmod(copied_config_abs, stat.S_IRUSR | stat.S_IWUSR)

    def _install_config(self):
        self.start_event('Processing configuration')
        self.add_log_line(f'Parsing config {self._config_file} file')

        with open(self._config_file) as f:
            config_str = f.read()

        if not config_str:
            raise InstallerException(f'Config is empty')

        config = yaml.safe_load(config_str)
        self.add_log_line(f'Using new root {self.TARGET_ROOT}')
        storage_installer = StorageInstaller(target_root=self.TARGET_ROOT,
                                             config=config, event_receiver=self)
        efi_mount = storage_installer.efi_mount_point
        pkgs_installer = PackagesInstaller(target_root=self.TARGET_ROOT,
                                           config=config, event_receiver=self)

        installers = [
            storage_installer,
            RepoInstaller(target_root=self.TARGET_ROOT, config=config, event_receiver=self),
            ProxyInstaller(target_root=self.TARGET_ROOT, config=config, event_receiver=self),
            pkgs_installer,
            ServicesInstaller(target_root=self.TARGET_ROOT, config=config, event_receiver=self),
            SwapfileInstaller(target_root=self.TARGET_ROOT, config=config, event_receiver=self),
            TimezoneInstaller(target_root=self.TARGET_ROOT, config=config, event_receiver=self),
            UsersInstaller(target_root=self.TARGET_ROOT, config=config, event_receiver=self),
            NetworkInstaller(target_root=self.TARGET_ROOT, config=config, event_receiver=self),
            KernelInstaller(target_root=self.TARGET_ROOT, config=config, event_receiver=self),
            BootloaderInstaller(target_root=self.TARGET_ROOT, config=config, event_receiver=self,
                                efi_mount=efi_mount),
            SecureBootInstaller(target_root=self.TARGET_ROOT, config=config, event_receiver=self),
        ]

        for i in installers:
            pkgs_installer.add_package(*i.packages)

        for i in installers:
            i.apply()

        for i in installers:
            i.post_apply()

        self._copy_yaml_config()

        for i in reversed(installers):
            i.cleanup()

        self.start_event('\nInstallation complete!')


class ConsoleInstallerController(BaseInstallerController):
    def __init__(self, app: Application, config_file):
        super().__init__(app, False, config_file)

    def run(self):
        try:
            self._run()
        except Exception as err:
            print(err_msg_with_debug_log_file(f'{err}', app=self._app))
            return 1
        return 0

    def start_event(self, msg):
        print(msg)
        log.debug(msg)

    def stop_event(self):
        pass

    def add_log_line(self, msg):
        # No need to litter the stdout. If you need details, just enable debugging.
        log.debug(msg)


class InstallerController(BaseInstallerController):
    def __init__(self, app: Application, create_config=True, config_file=DEFAULT_CONFIG_FILE):
        super().__init__(app, create_config, config_file)
        self._view = InstallerView(self, iso_mode=self._app.iso_mode)
        self._eloop = asyncio.get_event_loop()

    def create_config(self):
        self.add_log_line(f'Creating config {self._config_file} file')
        with open(self._config_file, 'w') as f:
            for c in self._app.controllers():
                yaml_str = c.to_yaml()
                if yaml_str:
                    f.write(yaml_str + '\n')

    async def _start(self):
        try:
            await run_in_thread(self._run)
        except Exception as err:
            self._event_start(err_msg_with_debug_log_file(f'{err}', app=self._app))
            self._event_finish()
            self._view.done()
            return

        self._event_finish()
        self._view.done()

    def add_log_line(self, msg):
        self._eloop.call_soon_threadsafe(self._add_log_line, msg)
        log.debug(msg)

    def start_event(self, msg):
        self._eloop.call_soon_threadsafe(self._event_start, msg)
        log.debug(msg)

    def stop_event(self):
        self._eloop.call_soon_threadsafe(self._event_finish)

    def _event_start(self, msg):
        self._view.add_log_line(msg)
        self._event_finish()
        self._view.event_start('', '', msg)

    def _event_finish(self):
        self._view.event_finish('')

    def _add_log_line(self, msg):
        self._view.add_log_line(msg)

    def click_cancel(self):
        self._app.exit()

    def click_reboot(self):
        self._app.reboot()

    def click_poweroff(self):
        self._app.poweroff()

    def make_ui(self):
        self._event_start('Starting installation')
        self._app.aio_loop.create_task(self._start())
        return self._view