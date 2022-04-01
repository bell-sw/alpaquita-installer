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

        self._event_receiver.start_event(f'Installing packages: {self.packages}')
        res = run_cmd(args=args)
        self._event_receiver.add_log_line('{}'.format(res.stdout.decode()))

    def post_apply(self):
        # Can be in apply(). It's just a matter of taste
        self._event_receiver.start_event('Enabling base services')
        for svc, runlevel in [('agetty.tty1', 'boot'),
                              ('acpid', 'default'),
                              ('bootmisc', 'boot'),
                              ('crond', 'default'),
                              ('dmesg', 'sysinit'),
                              ('hostname', 'boot'),
                              ('hwclock', 'boot'),
                              ('killprocs', 'shutdown'),
                              ('modules', 'boot'),
                              ('mount-ro', 'shutdown'),
                              ('networking', 'boot'),
                              ('savecache', 'shutdown'),
                              ('swap', 'boot'),
                              ('sysctl', 'boot'),
                              ('syslog', 'boot'),
                              ('udev', 'sysinit'),
                              ('udev-settle', 'sysinit'),
                              ('udev-trigger', 'sysinit'),
                              ('urandom', 'boot')]:
            self.enable_service(service=svc, runlevel=runlevel)
