import logging

log = logging.getLogger('installer')

class InstallerException(Exception):
    pass

class Installer:
    def __init__(self, name, config):
        self._name = name
        if name not in config:
            raise InstallerException(f'Not found {name} in config')

        self._data = config.get(name)

    def apply(self):
        pass

    def pre_packages(self):
        return []

    def packages(self):
        return []
