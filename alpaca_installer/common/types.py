# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2020 Canonical, Ltd.

import enum


class ApplicationState(enum.Enum):
    STARTING_UP = enum.auto()
    CLOUD_INIT_WAIT = enum.auto()
    EARLY_COMMANDS = enum.auto()
    WAITING = enum.auto()
    NEEDS_CONFIRMATION = enum.auto()
    RUNNING = enum.auto()
    POST_WAIT = enum.auto()
    POST_RUNNING = enum.auto()
    UU_RUNNING = enum.auto()
    UU_CANCELLING = enum.auto()
    DONE = enum.auto()
    ERROR = enum.auto()
    EXITED = enum.auto()
