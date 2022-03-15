from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import enum

import attrs

from .file_system import FSType
from .utils import run_cmd, get_block_device_uuid, get_block_device_size

if TYPE_CHECKING:
    from .storage_device import StorageDevice


class StorageUnitFlag(enum.Enum):
    ESP = 1


@attrs.define
class StorageUnit:
    id: str
    size: int  # In bytes, updated by create_partitions and co
    fs_type: Optional[FSType]
    mount_point: Optional[str]
    storage_device: StorageDevice
    fs_opts: list[str] = attrs.field(default=attrs.Factory(list))
    # esp, boot flags
    flags: set[StorageUnitFlag] = attrs.field(default=attrs.Factory(set))

    block_device: Optional[str] = None
    fs_uuid: Optional[str] = None  # Updated by make_fs()

    # Used internally
    use_all_available_space: bool = False

    def is_flag_set(self, flag: StorageUnitFlag):
        return flag in self.flags

    def make_fs(self):
        if self.fs_type is None:
            return
        if self.block_device is None:
            raise RuntimeError('{}: no block device associated'.format(self))

        if self.fs_type == FSType.PHYSICAL_VOLUME:
            run_cmd(['pvremove', '-ff', '-y', self.block_device])
            args = ['pvcreate', '-f', '-y']
        elif self.fs_type == FSType.RAID_MEMBER:
            args = ['mdadm', '--misc', '-f', '--zero-superblock']
        elif self.fs_type == FSType.SWAP:
            args = ['mkswap']
        elif self.fs_type == FSType.EXT4:
            args = ['mkfs.ext4', '-F']
        elif self.fs_type == FSType.XFS:
            args = ['mkfs.xfs', '-f']
        elif self.fs_type == FSType.VFAT:
            args = ['mkfs.fat', '-F32']
        else:
            raise RuntimeError("Don't know how to create a file system on {}".format(self.block_device))
        args.append(self.block_device)
        run_cmd(args)

        if self.fs_type == FSType.RAID_MEMBER:
            return

        self.fs_uuid = get_block_device_uuid(self.block_device)


@attrs.define
class Partition(StorageUnit):
    crypto_passphrase: Optional[str] = None

    @property
    def gpt_type_guid(self) -> str:
        if self.is_flag_set(StorageUnitFlag.ESP):
            res = 'C12A7328-F81F-11D2-BA4B-00A0C93EC93B'
        elif self.fs_type == FSType.RAID_MEMBER:
            res = 'A19D880F-05FC-4D3B-A006-743F0F84911E'
        elif self.fs_type == FSType.PHYSICAL_VOLUME:
            res = 'E6D6D379-F507-44C2-A23C-238F2A3DF928'
        elif self.fs_type == FSType.SWAP:
            res = '0657FD6D-A4AB-43C4-84E5-0933C84B4F4F'
        else:
            res = '0FC63DAF-8483-4772-8E79-3D69D8477DE4'

        return res

    def make_fs(self):
        if self.fs_type == FSType.CRYPTO_PARTITION:
            if not self.block_device:
                raise RuntimeError('{}: no block device associated'.format(self))

            run_cmd(['cryptsetup', 'luksFormat', self.block_device],
                    input=self.crypto_passphrase.encode())
            self.fs_uuid = get_block_device_uuid(self.block_device)
        else:
            super().make_fs()


@attrs.define
class LogicalVolume(StorageUnit):
    pass


@attrs.define
class CryptoVolume(StorageUnit):
    # Default value here is a workaround for attrs inheritance
    partition: Partition = None

    def open(self):
        run_cmd(['cryptsetup', 'open', self.partition.block_device, self.id],
                input=self.partition.crypto_passphrase.encode())
        self.size = get_block_device_size(self.block_device)

    def close(self):
        run_cmd(['cryptsetup', 'close', self.block_device])
