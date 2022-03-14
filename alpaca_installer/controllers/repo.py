import urllib
import yaml
import logging
from .controller import Controller
from alpaca_installer.views.repo import RepoView

log = logging.getLogger('controllers.repo')

class RepoException(Exception):
    pass

class RepoController(Controller):
    def __init__(self, app):
        super().__init__(app)
        self._repo_base_url = 'https://packages.bell-sw.com'
        self._repos = []
        self._release = self.get_os_release().get('VERSION_ID', '').split('.')[0]
        self._release = 'v' + self._release if self._release else 'stream'

    def get_os_release(self):
        res = {}
        with open('/etc/os-release') as f:
            for line in f:
                k,v = line.rstrip().split('=')
                res[k] = v
        return res

    def make_ui(self):
        return RepoView(self, self._repo_base_url)

    def done(self, repo_base_url: str):
        self._repo_base_url = repo_base_url
        self._app.next_screen()

    def cancel(self):
        self._app.prev_screen()

    def get_repos(self, url):
        self._repos = []
        for name in [ 'core', 'universe' ]:
            self._repos.append(urllib.parse.quote(f'{url}/alpaca/{self._release}/{name}', safe='/:'))
        return self._repos

    def to_yaml(self):
        yaml_data = yaml.dump({ "repositories" : self._repos })

        log.debug(f"export to yaml: {yaml_data}")
        return yaml_data
