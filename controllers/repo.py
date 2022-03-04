import os
import urllib
import yaml
import logging
from views.repo import RepoView

log = logging.getLogger('controllers.repo')

class RepoException(Exception):
    pass

class RepoInstaller:
    def apply(self, data):
        try:
            repos = yaml.safe_load(data).get('repositories',[])
        except yaml.YAMLError as err:
            log.error(f"Error: {err}")
            raise RepoException(f'Error in loading yaml: {err}')
        except:
            raise RepoException('Error in parsing repositories')

        log.info(f"Installing repos: {repos}")

        with open('/etc/apk/repositories', 'a') as apk_repo_file:
            for r in repos:
                apk_repo_file.write('\n' + r)
            apk_repo_file.write('\n')
            return

        raise RepoException("Failed to add repositories")

class RepoController:
    def __init__(self, app):
        self.app = app
        self.repo_base_url = 'https://packages.bell-sw.com'
        self.repos = []
        self.installer = RepoInstaller()

    def make_ui(self):
        return RepoView(self, self.repo_base_url)

    def done(self, repo_base_url: str):
        self.repo_base_url = repo_base_url
        self.app.next_screen()

    def cancel(self):
        self.app.prev_screen()

    def get_repos(self, url):
        # TODO: Need to source & export /etc/os-release
        # set -o allexport && source /etc/os-release; set +o allexport
        major_ver = os.getenv('VERSION_ID', '').split('.')[0]

        self.repos = []
        for name in [ 'core', 'universe' ]:
            self.repos.append(urllib.parse.quote(f'{url}/alpaca/v{major_ver}/{name}', safe='/:'))

        self.to_yaml()
        return self.repos

    def to_yaml(self):
        yaml_data = yaml.dump({ "repositories" : self.repos })

        log.info(f"export to yaml: {yaml_data}")
        return yaml_data

    def get_installer(self):
        return self.installer
