#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Iterable, Collection, cast
import time
import os
import json
import abc
import logging

from .file_system import FSType
from .storage_unit import Partition, StorageUnitFlag
from .utils import get_block_device_size
from alpaquita_installer.common.utils import run_cmd

if TYPE_CHECKING:
    from .storage_unit import StorageUnit
    from .manager import StorageManager

log = logging.getLogger('smanager.storage_device')

DEVICE_CREATION_TIMEOUT = 10.0


class StorageDevice(abc.ABC):
    def __init__(self, manager: StorageManager, id: str):
        self._manager = manager
        self._id = id
        self._storage_units: list[StorageUnit] = []

    def __str__(self) -> str:
        return 'Storage device {}'.format(self.id)

    def __repr__(self) -> str:
        return str(self)

    def get_unit_by_id(self, id: str) -> Optional[StorageUnit]:
        for unit in self.storage_units:
            if unit.id == id:
                return unit
        return None

    @property
    def manager(self) -> StorageManager:
        return self._manager

    @property
    def id(self) -> str:
        return self._id

    @property
    def storage_units(self) -> Collection[StorageUnit]:
        return self._storage_units[:]

    def _add_storage_unit(self, unit: StorageUnit):
        if self.get_unit_by_id(unit.id):
            raise ValueError("{} already contains id '{}'".format(self, unit.id))

        if unit.mount_point and (not unit.fs_type):
            raise ValueError("{}: fs_type is not set for '{}' mount point".format(
                self, unit.mount_point))

        if unit.mount_point is not None:
            self.manager.check_can_mount_to(unit.mount_point)

        self._storage_units.append(unit)


class StorageDeviceOfLimitedSize(StorageDevice):
    def __init__(self, manager: StorageManager, id: str, size: int):
        super().__init__(manager=manager, id=id)
        if size <= 0:
            raise ValueError('size must be positive')

        self._size = size
        self._available = size

    def __str__(self) -> str:
        return 'Storage device {} with size {}'.format(self.id, self.size)

    @property
    def size(self) -> int:
        return self._size

    @property
    def available(self) -> int:
        return self._available

    def _add_storage_unit(self, unit: StorageUnit):
        if (self.available == 0) or (self.available < unit.size):
            raise ValueError('{}: not enough free space'.format(self))

        if unit.size == 0:
            unit.size = self.available
            unit.use_all_available_space = True
        self._available -= unit.size

        super()._add_storage_unit(unit)


class StorageDeviceWithPartitions(StorageDeviceOfLimitedSize):
    def __init__(self, manager: StorageManager, id: str, size: int):
        super().__init__(manager=manager, id=id, size=size)
        self._partitions_created = False
        self._block_device = id
        self._esp_defined = False

    @property
    def partitions(self) -> Collection[Partition]:
        return cast(Collection[Partition], self.storage_units)

    @property
    def block_device(self) -> str:
        return self._block_device

    def add_partition(self, id: str, fs_type: Optional[FSType] = None,
                      size: int = 0, mount_point: Optional[str] = None,
                      fs_opts: Optional[Iterable[str]] = None,
                      flags: Optional[Iterable[StorageUnitFlag]] = None,
                      crypto_passphrase: Optional[str] = None) -> Partition:
        if not id:
            raise ValueError('Cannot create a partition without an id')

        if fs_type == FSType.CRYPTO_PARTITION:
            if not crypto_passphrase:
                raise ValueError('Cannot create a crypto partition without a passphrase')
            if fs_opts or mount_point:
                raise ValueError('fs opts or mount point is set')

        opts = set()
        if fs_opts:
            opts = set(fs_opts)

        if not flags:
            flags = []
        for flag in flags:
            if flag == StorageUnitFlag.ESP:
                if self._esp_defined:
                    raise ValueError('{}: ESP already defined'.format(self))
                if fs_type != FSType.VFAT:
                    raise ValueError('ESP is supported only on the VFAT file system')
                self._esp_defined = True

        part = Partition(id=id, size=size, fs_type=fs_type, fs_opts=opts,
                         mount_point=mount_point, storage_device=self,
                         flags=flags[:], crypto_passphrase=crypto_passphrase)

        self._add_storage_unit(part)
        log.debug('{}: added {}'.format(self, part))
        return part

    def create_partitions(self):
        log.debug('{}: creating partitions'.format(self))
        run_cmd(args=['wipefs', '-a', self.block_device])

        script = ['label: gpt']
        for part in self.partitions:
            line = 'type={}'.format(part.gpt_type_guid)
            if not part.use_all_available_space:
                line = 'size={}KiB,{}'.format(part.size // 1024, line)
            script.append(line)
        script = '\n'.join(script)

        args = ['sfdisk', '--lock', '--wipe', 'always',
                '--wipe-partitions', 'always',
                '--no-reread', '--no-tell-kernel', self.block_device]
        run_cmd(args=args, input=script.encode())

        res = run_cmd(args=['sfdisk', '-J', self.block_device])
        ptable = json.loads(res.stdout)['partitiontable']
        items = ptable.get('partitions', [])
        if len(items) != len(self.partitions):
            raise RuntimeError("{}: {} partitions created, {} expected".format(
                self, len(items), len(self.partitions)))

        block_devices = []
        for i, part in enumerate(self.partitions):
            block_device = items[i]['node']
            part.block_device = block_device
            block_devices.append(block_device)

        # It turns out that 'blockdev --rereadpt' + 'mdev -s' are not enough.
        # We need to wait and periodically check that all block devices are created.
        spent_time = 0.0
        sleep_interval = 0.1
        created = False
        while spent_time < DEVICE_CREATION_TIMEOUT:
            if all(os.path.exists(d) for d in block_devices):
                created = True
                break

            run_cmd(args=['blockdev', '--rereadpt', self.block_device])

            time.sleep(sleep_interval)
            spent_time += sleep_interval

        if not created:
            raise RuntimeError('{}: not all partition block devices were created'.format(self))

        for part in self.partitions:
            part.size = get_block_device_size(part.block_device)

        self._partitions_created = True
