import os
import re

from .installer import Installer
from .utils import read_key_or_fail

# Optional
#
# kernel:
#   cmdline: [ 'quiet' ]
#


class KernelInstaller(Installer):
    def __init__(self, target_root: str, config: dict, event_receiver):
        super().__init__(name='kernel', config=config,
                         event_receiver=event_receiver,
                         data_type=dict, data_is_optional=True,
                         target_root=target_root)

        self._cmdline: list[str] = []
        if self._data is not None:
            self._cmdline = read_key_or_fail(self._data, 'cmdline', str)
            if not all(isinstance(x, str) for x in self._cmdline):
                raise ValueError("All 'cmdline' elements must be strings")
        if not self._cmdline:
            self._cmdline = ['quiet']

        self.add_package('linux-lts')

    def apply(self):
        pass

    def post_apply(self):
        self._event_receiver.start_event('Regenerating initrd')

        kver = None
        for name in os.listdir(self.abs_target_path('/boot')):
            m = re.match(r'^config-(\d+.*)$', name)
            if m:
                kver = m.group(1)
                break
        if not kver:
            raise RuntimeError('Unable to determine the installed kernel version')
        self.run_in_chroot(args=['dracut', '-f', '/boot/initramfs-lts', kver])

        data = """GRUB_DISTRIBUTOR="Alpaca"
GRUB_TIMEOUT=2
GRUB_DISABLE_SUBMENU=y
GRUB_DISABLE_RECOVERY=true
GRUB_CMDLINE_LINUX_DEFAULT="{}"
""".format(' '.join(self._cmdline))
        with open(self.abs_target_path('/etc/default/grub'), 'w') as file:
            file.write(data)
