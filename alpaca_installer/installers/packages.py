# TODO: importing from nmanager here looks odd
from alpaca_installer.nmanager.utils import run_cmd
from .installer import Installer, InstallerException


class PackagesInstaller(Installer):
    def __init__(self, target_root: str, config: dict):
        yaml_key = 'extra_packages'
        super().__init__(name=yaml_key, config=config,
                         target_root=target_root,
                         data_is_optional=True)
        if self._data:
            if not isinstance(self._data, list):
                raise InstallerException("'{}' must be a YAML array".format(yaml_key))
            for pkg in self._data:
                self.add_package(pkg)

        self.add_package('alpaca-base')

    def apply(self):
        common = ['apk', 'add', '--root', self.target_root,
                  '--no-progress', '--quiet']

        run_cmd(args=(common + ['--initdb']))

        args = common + ['--keys',
                         '/etc/apk/keys',  # install using keys from the host system
                         '--update-cache', '--clean-protected']
        args.extend(self.packages)
        run_cmd(args=args)
