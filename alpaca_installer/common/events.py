#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

import abc

class EventReceiver(abc.ABC):

    @abc.abstractmethod
    def start_event(self, msg):
        pass

    @abc.abstractmethod
    def stop_event(self):
        pass

    @abc.abstractmethod
    def add_log_line(self, msg):
        pass
