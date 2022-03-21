import logging
import abc
from typing import Collection

log = logging.getLogger('installer')


class InstallerException(Exception):
    pass

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

class Installer(abc.ABC):
    def __init__(self, name: str, config: dict,
                 target_root: str,
                 event_receiver: EventReceiver,
                 data_type,
                 data_is_optional: bool = False):
        self._name = name
        self._packages = set()
        self._target_root = target_root
        self._event_receiver = event_receiver

        if (not data_is_optional) and (name not in config):
            raise InstallerException(f'Not found {name} in config')
        self._data = config.get(name, None)
        if (self._data is not None) and (not isinstance(self._data, data_type)):
            raise InstallerException("'{}' is of type '{}', expected '{}'".format(
                name, type(self._data), data_type))

    @abc.abstractmethod
    def apply(self):
        pass

    @property
    def target_root(self) -> str:
        return self._target_root

    def pre_packages(self):
        return []

    @property
    def packages(self) -> Collection[str]:
        return set(self._packages)

    def add_package(self, *names: Collection[str]):
        self._packages.update(names)
