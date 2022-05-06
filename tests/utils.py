#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

from typing import Type, TypeVar

from alpaca_installer.common.events import EventReceiver


class StubEventReceiver(EventReceiver):
    def start_event(self, msg):
        pass

    def stop_event(self):
        pass

    def add_log_line(self, msg):
        pass


_InstallerType = TypeVar('_InstallerType')


def new_installer(installer_cls: Type[_InstallerType], **kwargs) -> _InstallerType:
    if 'target_root' not in kwargs:
        kwargs['target_root'] = 'target_root'
    if 'event_receiver' not in kwargs:
        kwargs['event_receiver'] = StubEventReceiver()
    return installer_cls(**kwargs)
