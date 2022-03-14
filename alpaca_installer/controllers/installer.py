from gettext import install
import yaml
import logging
from alpaca_installer.views.installer import InstallerView
from alpaca_installer.installers.repo import RepoInstaller
from alpaca_installer.installers.installer import InstallerException
from .controller import Controller

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

            installers = [
                RepoInstaller(config)
            ]
        except yaml.YAMLError as err:
            log.error(f"Error: {err}")
            raise InstallerException(f'Error in loading yaml: {err}')
        except InstallerException as err:
            raise InstallerException(f'Error in parsing config: {err}')

        for i in installers:
            i.apply()
