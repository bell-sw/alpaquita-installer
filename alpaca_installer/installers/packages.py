# TODO: importing from nmanager here looks odd
from alpaca_installer.nmanager.utils import run_cmd
from .installer import Installer, InstallerException


class PackagesInstaller(Installer):
    def __init__(self, target_root: str, config: dict, event_receiver):
        super().__init__(name='extra_packages', config=config,
                         event_receiver=event_receiver,
                         target_root=target_root,
                         data_type=list,
                         data_is_optional=True)
        if self._data:
            for pkg in self._data:
                self.add_package(pkg)

        self.add_package('acct', 'alpaca-base')

    def apply(self):
        self._event_receiver.start_event('Initializing new root')

        common = ['apk', 'add', '--root', self.target_root,
                  '--keys', '/etc/apk/keys', # install using keys from the host system
                  '--no-progress']

        res = run_cmd(args=(common + ['--initdb']))
        self._event_receiver.add_log_line('{}'.format(res.stdout.decode()))

        args = common + ['--update-cache', '--clean-protected']
        args.extend(self.packages)

        self._event_receiver.start_event(f'Installing packages: {sorted(self.packages)}')
        res = run_cmd(args=args)
        self._event_receiver.add_log_line('{}'.format(res.stdout.decode()))
