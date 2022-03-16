from gettext import install
import yaml
import logging
import urwid
from alpaca_installer.views.installer import InstallerView
from alpaca_installer.installers.repo import RepoInstaller
from alpaca_installer.installers.packages import PackagesInstaller
from alpaca_installer.installers.users import UsersInstaller
from alpaca_installer.installers.installer import InstallerException
from .controller import Controller
# TODO: do something with this run_cmd
from alpaca_installer.nmanager.utils import run_cmd

log = logging.getLogger('controllers.installer')


class InstallerController(Controller):
    def __init__(self, app, create_config=True, config_file='setup.yaml'):
        super().__init__(app)
        self._config_file = config_file
        self._create_config = create_config

    def make_ui(self):
       return InstallerView(self)

    def cancel(self):
        pass

    def done(self):
        if self._create_config:
            self.create_config()
        self.install_config()

        # TODO: this is temporary
        raise urwid.ExitMainLoop

    def create_config(self):
        with open(self._config_file, 'w') as f:
            for c in self._app.controllers():
                yaml_str = c.to_yaml();
                if yaml_str:
                    f.write(yaml_str + '\n')

    def install_config(self):
        try:
            with open(self._config_file) as f:
                config_str = f.read()
        except IOError as err:
            raise InstallerException(f'Failed to open/read config file: {err}')

        if not config_str:
            raise InstallerException(f'Config is empty')

        try:
            config = yaml.safe_load(config_str)
            target_root = '/mnt/target_root'
            pkgs_installer = PackagesInstaller(target_root=target_root,
                                              config=config)

            installers = [
                RepoInstaller(target_root=target_root, config=config),
                pkgs_installer,
                UsersInstaller(target_root=target_root, config=config),
            ]
        except yaml.YAMLError as err:
            log.error(f"Error: {err}")
            raise InstallerException(f'Error in loading yaml: {err}')
        except InstallerException as err:
            raise InstallerException(f'Error in parsing config: {err}')

        for i in installers:
            pkgs_installer.add_package(*i.packages)

        # TODO: in the future this will be handled by an installer, which
        # will mount all necessary file systems to target_root
        # Now these commands are just for testing purposes
        run_cmd(args=['rm', '-rf', target_root])
        run_cmd(args=['mkdir', '-p', target_root])

        for i in installers:
            i.apply()
