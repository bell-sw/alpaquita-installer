import os
import logging

from .installer import Installer

log = logging.getLogger('installer.repo')


class RepoInstaller(Installer):
    def __init__(self, target_root: str, config: dict):
        super().__init__(name='repositories', target_root=target_root,
                         config=config)

    def apply(self):
        apk_dir = os.path.join(self.target_root, 'etc/apk')
        os.makedirs(apk_dir, exist_ok=True)
        repo_file = os.path.join(apk_dir, 'repositories')
        with open(repo_file, 'a') as apk_repo_file:
            for r in self._data:
                apk_repo_file.write('\n' + r)
            apk_repo_file.write('\n')
