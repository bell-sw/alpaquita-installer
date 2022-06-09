#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

from .installer import Installer
from .utils import read_list


# Optional
#
# At first the 'disabled' list is processed, then the 'enabled' one
#
# services:
#   disabled: ['svc1', 'svc2']
#   enabled: ['svc3']
#


class ServicesInstaller(Installer):
    def __init__(self, target_root: str, config: dict, event_receiver):
        yaml_tag = 'services'
        super().__init__(name=yaml_tag, config=config,
                         event_receiver=event_receiver,
                         data_type=dict, data_is_optional=True,
                         target_root=target_root)

        lists = {'disabled': [], 'enabled': []}

        if self._data is not None:
            for name in lists:
                if name not in self._data:
                    continue

                lists[name] = read_list(self._data, key=name, item_type=str,
                                        error_label=f'{yaml_tag}/{name}')

        self._disabled = lists['disabled']
        self._enabled = lists['enabled']

    def apply(self):
        pass

    def post_apply(self):
        self._event_receiver.start_event('Enabling base services')
        for svc, runlevel in [('agetty.tty1', 'boot'),
                              ('acpid', 'default'),
                              ('bootmisc', 'boot'),
                              ('crond', 'default'),
                              ('dmesg', 'sysinit'),
                              ('hostname', 'boot'),
                              ('hwclock', 'boot'),
                              ('killprocs', 'shutdown'),
                              ('modules', 'boot'),
                              ('mount-ro', 'shutdown'),
                              ('networking', 'boot'),
                              ('savecache', 'shutdown'),
                              ('swap', 'boot'),
                              ('sysctl', 'boot'),
                              ('syslog', 'boot'),
                              ('udev', 'sysinit'),
                              ('udev-settle', 'sysinit'),
                              ('udev-trigger', 'sysinit'),
                              ('urandom', 'boot')]:
            self.enable_service(service=svc, runlevel=runlevel)

        if self._disabled:
            self._event_receiver.start_event('Disabling services: {}'.format(sorted(self._disabled)))

            for svc in self._disabled:
                self.disable_service(service=svc, runlevel='default')

        if self._enabled:
            self._event_receiver.start_event('Enabling services: {}'.format(sorted(self._enabled)))

            for svc in self._enabled:
                self.enable_service(service=svc, runlevel='default')
