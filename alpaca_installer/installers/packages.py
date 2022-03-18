# TODO: importing from nmanager here looks odd
from alpaca_installer.nmanager.utils import run_cmd
from .installer import Installer, InstallerException


class PackagesInstaller(Installer):
    def __init__(self, target_root: str, config: dict, event_receiver):
        yaml_key = 'extra_packages'
        super().__init__(name=yaml_key, config=config,
                         event_receiver=event_receiver,
                         target_root=target_root,
                         data_is_optional=True)
        if self._data:
            if not isinstance(self._data, list):
                raise InstallerException("'{}' must be a YAML array".format(yaml_key))
            for pkg in self._data:
                self.add_package(pkg)

        self.add_package('alpaca-base')

    def apply(self):
        self._event_receiver.start_event('Initializing new root')

        common = ['apk', 'add', '--root', self.target_root,
                  '--keys', '/etc/apk/keys', # install using keys from the host system
                  '--no-progress']

        res = run_cmd(args=(common + ['--initdb']))
        self._event_receiver.add_log_line('{}'.format(res.stdout.decode()))

        args = common + ['--update-cache', '--clean-protected']
        args.extend(self.packages)

        self._event_receiver.start_event(f'Installing packages: {self.packages}')
        res = run_cmd(args=args)
        self._event_receiver.add_log_line('{}'.format(res.stdout.decode()))
