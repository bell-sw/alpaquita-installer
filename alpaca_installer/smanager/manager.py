#  SPDX-FileCopyrightText: 2022 BellSoft
#  SPDX-License-Identifier:  AGPL-3.0-or-later

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Iterable, TypeVar, Type
from collections.abc import Collection
from itertools import chain
import os

from .disk import Disk
from .lvm import VolumeGroup
from .raid import RAID
from .cryptsetup import Cryptsetup
from .storage_unit import Partition
from .file_system import FSType
from .utils import run_cmd

if TYPE_CHECKING:
    from .storage_device import StorageDevice
    from .storage_unit import StorageUnit, CryptoVolume

_DEVICE_TYPE = TypeVar('_DEVICE_TYPE')


class StorageManager:
    def __init__(self):
        self._devices: dict[str, StorageDevice] = dict()
        self._mount_root_base: Optional[str] = None

        self._cryptsetup = Cryptsetup(id='__cryptsetup__', manager=self)
        self._devices[self._cryptsetup.id] = self._cryptsetup

    def _get_unit_by_mount_point(self, mount_point: str) -> Optional[StorageUnit]:
        for device in self._devices.values():
            for unit in device.storage_units:
                if unit.mount_point == mount_point:
                    return unit
        return None

    def _path_relative_to_mount_root_base(self, path: str):
        if self.mount_root_base:
            if os.path.isabs(path):
                path = path.lstrip('/')
            return os.path.join(self.mount_root_base, path)
        else:
            return path

    def check_can_mount_to(self, mount_point: str):
        if not os.path.isabs(mount_point):
            raise ValueError('{}: must be an absolute path'.format(mount_point))

        if self._get_unit_by_mount_point(mount_point):
            raise ValueError("Mount point '{}' is already defined".format(mount_point))

    @property
    def mount_root_base(self) -> Optional[str]:
        return self._mount_root_base

    @mount_root_base.setter
    def mount_root_base(self, value):
        self._mount_root_base = value

    @property
    def devices(self) -> set[StorageDevice]:
        return set(self._devices.values())

    @property
    def storage_units(self) -> Collection[StorageUnit]:
        res = []
        for device in self.devices:
            for unit in device.storage_units:
                res.append(unit)
        return res

    @property
    def mount_points(self) -> Collection[tuple[str, StorageUnit]]:
        res = []
        for unit in self.storage_units:
            if unit.mount_point:
                res.append((unit.mount_point, unit))
        return res

    @property
    def cryptsetup(self) -> Cryptsetup:
        return self._cryptsetup

    def get_unit_by_mount_point(self, mount_point: str) -> Optional[StorageUnit]:
        for mnt, unit in self.mount_points:
            if mount_point == mnt:
                return unit
        return None

    def get_device_by_id(self, id: str) -> Optional[StorageDevice]:
        return self._devices.get(id, None)

    def get_devices_by_type(self, device_type: Type[_DEVICE_TYPE]) -> Collection[_DEVICE_TYPE]:
        return tuple(d for d in self._devices.values() if isinstance(d, device_type))

    def add_disk(self, id: str) -> Disk:
        device = self.get_device_by_id(id)
        if device:
            raise ValueError("{} already exists".format(device))
        disk = Disk(manager=self, id=id)
        self._devices[id] = disk
        return disk

    def add_vg(self, id: str, physical_volumes: Iterable[Partition | CryptoVolume]) -> VolumeGroup:
        device = self.get_device_by_id(id)
        if device:
            raise ValueError("{} already exists".format(device))
        vg = VolumeGroup(manager=self, id=id, physical_volumes=physical_volumes)
        self._devices[id] = vg
        return vg

    def add_raid(self, id: str, level: int, members: Iterable[Partition | CryptoVolume],
                 metadata: str = '1.2') -> RAID:
        device = self.get_device_by_id(id)
        if device:
            raise ValueError('{} already exists'.format(device))
        raid = RAID(manager=self, id=id, metadata=metadata, level=level, members=members)
        self._devices[id] = raid
        return raid

    def create_filesystems(self):
        for disk in self.get_devices_by_type(Disk):
            disk.create_partitions()
            for part in disk.partitions:
                part.make_fs()

        self.cryptsetup.open_volumes()
        for volume in self.cryptsetup.volumes:
            volume.make_fs()

        for raid in self.get_devices_by_type(RAID):
            raid.create_partitions()
            for part in raid.partitions:
                part.make_fs()

        for vg in self.get_devices_by_type(VolumeGroup):
            vg.create_logical_volumes()
            for lv in vg.logical_volumes:
                lv.make_fs()

    def mount(self):
        items = sorted(self.mount_points, key=lambda x: x[0])
        for mount_point, unit in items:
            mnt_dir = self._path_relative_to_mount_root_base(mount_point)

            run_cmd(args=['mkdir', '-p', mnt_dir])
            run_cmd(args=['mount', '-t', str(unit.fs_type), unit.block_device, mnt_dir])

    def unmount(self):
        items = sorted(self.mount_points, key=lambda x: x[0], reverse=True)
        for mount_point, _ in items:
            mnt_dir = self._path_relative_to_mount_root_base(mount_point)
            run_cmd(args=['umount', mnt_dir])

    def write_mdadm_conf(self, path: str):
        res = run_cmd(args=['mdadm', '--detail', '--scan'])
        if not res.stdout:
            raise RuntimeError('mdadm did not find any RAID devices')

        with open(path, 'wb') as file:
            file.write(res.stdout)

    def write_fstab(self, path: str):
        swap_units = [u for u in self.storage_units if u.fs_type == FSType.SWAP]
        mount_units = [x[1] for x in sorted(self.mount_points, key=lambda x: x[0])]

        with open(path, 'w') as file:
            for unit in chain(mount_units, swap_units):
                fs_spec = unit.fs_uuid

                if unit.fs_type == FSType.SWAP:
                    fs_file = 'none'
                else:
                    fs_file = unit.mount_point

                fs_vfstype = str(unit.fs_type)

                if (unit.fs_type == FSType.SWAP) or (not unit.fs_opts):
                    fs_mntopts = 'defaults'
                else:
                    fs_mntopts = ','.join(unit.fs_opts)

                fs_freq = 0

                if unit.fs_type == FSType.SWAP:
                    fs_passno = 0
                elif unit.mount_point == '/':
                    fs_passno = 1
                else:
                    fs_passno = 2

                file.write('UUID={} {} {} {} {} {}\n'.format(
                    fs_spec, fs_file, fs_vfstype, fs_mntopts, fs_freq, fs_passno))

    def write_dmcrypt(self, path: str):
        key_timeout = 1
        max_timeout = 300
        retries = 5

        volumes = [vol for vol in self.cryptsetup.volumes]
        swap = [vol for vol in volumes if vol.fs_type == FSType.SWAP]
        non_swap = [vol for vol in volumes if vol.fs_type != FSType.SWAP]

        lines = [
            'dmcrypt_key_timeout={}'.format(key_timeout),
            'dmcrypt_max_timeout={}'.format(max_timeout),
            'dmcrypt_retries={}'.format(retries)
        ]

        for vol in chain(swap, non_swap):
            lines.extend([
                '',
                'target={}'.format(vol.id),
                'source=UUID={}'.format(vol.partition.fs_uuid)
            ])

        # This is mandatory per the dmcrypt file format
        lines.append('')

        with open(path, 'w') as file:
            file.write('\n'.join(lines))
