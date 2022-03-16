import os
import datetime

from alpaca_installer.nmanager.utils import run_cmd
from alpaca_installer.models.user import UserModel
from .installer import Installer, InstallerException


def read_user_from_dict(data: dict) -> UserModel:
    name = data.get('name', None)
    password_hash = data.get('password', None)
    gecos = data.get('gecos', None)
    is_admin = data.get('is_admin', False)

    user = UserModel(name=name, gecos=gecos, is_admin=is_admin,
                     password=password_hash)

    # As it's a separator in /etc/shadow
    if ':' in user.password:
        raise ValueError("':' is prohibited in 'password'")

    return user


# TODO: this will probably be used by the root password installer
def update_user_hash(etc_shadow: str, user: str, password_hash: str):
    with open(etc_shadow, 'r') as file:
        lines = file.readlines()

    found_user = False
    for i, line in enumerate(lines):
        tokens = line.split(':')
        if tokens[0] != user:
            continue

        # Encrypted password
        tokens[1] = password_hash
        # Date of last password change (number of days since the Unix epoch)
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        tokens[2] = str((now - epoch).days)
        lines[i] = ':'.join(tokens)
        found_user = True

    if not found_user:
        raise RuntimeError("No user '{}' found in '{}'".format(user, etc_shadow))

    with open(etc_shadow, 'w') as file:
        file.writelines(lines)


class UsersInstaller(Installer):
    def __init__(self, target_root: str, config: dict):
        yaml_key = 'users'

        super().__init__(name=yaml_key, target_root=target_root,
                         config=config, data_is_optional=True)

        self._users: list[UserModel] = []

        if not self._data:
            return
        if not isinstance(self._data, list):
            raise InstallerException("'{}' must be a YAML array".format(yaml_key))

        for item in self._data:
            try:
                user = read_user_from_dict(item)
            except (TypeError, ValueError) as exc:
                raise InstallerException(str(exc)) from None
            if user.is_admin:
                self.add_package('sudo')
            self._users.append(user)

    def apply(self):
        wheel_sudoers_needed = False
        etc_shadow = os.path.join(self.target_root, 'etc/shadow')

        for user in self._users:
            args = ['chroot', self.target_root, 'adduser', '-D']
            if user.gecos:
                args.extend(['-g', user.gecos])
            args.append(user.name)
            run_cmd(args=args)

            update_user_hash(etc_shadow=etc_shadow, user=user.name,
                             password_hash=user.password)

            if user.is_admin:
                run_cmd(args=['chroot', self.target_root, 'addgroup',
                              user.name, 'wheel'])
                wheel_sudoers_needed = True

        if wheel_sudoers_needed:
            with open(os.path.join(self.target_root, 'etc/sudoers.d/wheel'), 'w') as file:
                file.write('%wheel ALL=(ALL) ALL\n')
