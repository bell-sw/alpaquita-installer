import os
import urllib
import yaml
import logging
from views.repo import RepoView
from installers.installer import Installer

log = logging.getLogger('installer.repo')

class RepoInstaller(Installer):
    def __init__(self, config):
        super().__init__('repositories', config)

    def apply(self):
        with open('/etc/apk/repositories', 'a') as apk_repo_file:
            for r in self._data:
                apk_repo_file.write('\n' + r)
            apk_repo_file.write('\n')
