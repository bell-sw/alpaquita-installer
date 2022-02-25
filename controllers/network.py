from __future__ import annotations
from typing import Optional, TYPE_CHECKING

import attrs

from views.network import NetworkView
from nmanager.interface import InterfaceInfo
from nmanager.ip_config import IPConfig4, IPConfig6
from nmanager.wifi_config import WIFIConfig

if TYPE_CHECKING:
    from installer.application import Application


class NetworkController:
    def __init__(self, app: Application):
        self._app = app
        self._iface_name = self._app.nmanager.get_selected_iface()

        self._ip_config = {
            4: IPConfig4(method='dhcp'),
            6: IPConfig6(method='disabled')
        }
        if self._iface_name:
            self._ip_config[4] = self._app.nmanager.get_ipv4_config()
            self._ip_config[6] = self._app.nmanager.get_ipv6_config()

        self._wifi_config: Optional[WIFIConfig] = None

    def make_ui(self):
        return NetworkView(self)

    async def _apply_configuration(self):
        try:
            apply_task = self._app.aio_loop.run_in_executor(None,
                                                            self._app.nmanager.apply)
            await self._app.wait_with_text_dialog(apply_task, 'Applying configuration')
            self._app.next_screen()
        except RuntimeError as exc:
            self._app.show_error_message(str(exc))

    def done(self):
        self._app.nmanager.select_iface(self._iface_name)
        self._app.nmanager.set_ipv4_config(self._ip_config[4])
        self._app.nmanager.set_ipv6_config(self._ip_config[6])

        if self.get_iface_info(self._iface_name).type == 'wifi':
            if not self._wifi_config:
                self._app.show_error_message('Wireless network is not configured')
                return
            self._app.nmanager.set_wifi_config(self._wifi_config)

        if self._app.nmanager.apply_required:
            self._app.aio_loop.create_task(self._apply_configuration())
        else:
            self._app.next_screen()

    def cancel(self):
        self._app.prev_screen()

    def select_iface(self, iface_name: str):
        self._iface_name = iface_name

    def get_selected_iface(self) -> Optional[str]:
        return self._iface_name

    def get_available_ifaces(self) -> set[str]:
        return self._app.nmanager.get_available_ifaces()

    def get_bond_candidates(self) -> set[str]:
        return self._app.nmanager.get_bond_candidates()

    def get_iface_info(self, iface_name: str) -> InterfaceInfo:
        return self._app.nmanager.get_iface_info(iface_name)

    def add_vlan_iface(self, base_iface_name: str, vlan_id: int):
        try:
            new_iface = self._app.nmanager.add_vlan_iface(base_iface_name, vlan_id)
            self._app.ui.body.update_interfaces_list(iface_to_select=new_iface)
            self._app.ui.body.remove_overlay()
        except ValueError as exc:
            self._app.show_error_message(str(exc))

    def add_bond_iface(self, name: str, members: list[str],
                       mode: str, hash_policy: Optional[str]):
        try:
            new_iface = self._app.nmanager.add_bond_iface(name=name, members=members,
                                                          mode=mode, hash_policy=hash_policy)
            self._app.ui.body.update_interfaces_list(iface_to_select=new_iface)
            self._app.ui.body.remove_overlay()
        except ValueError as exc:
            self._app.show_error_message(str(exc))

    def del_iface(self, iface_name: str):
        try:
            self._app.nmanager.del_iface(iface_name)
            self._app.ui.body.update_interfaces_list()
        except ValueError as exc:
            self._app.show_error_message(str(exc))

    def set_ip_config(self, ip_ver: int, data: dict[str, str]):
        try:
            if ip_ver not in (4, 6):
                raise ValueError(f'Unknown IP version {ip_ver}')

            if 'name_servers' in data:
                data['name_servers'] = data['name_servers'].split(',')
            if ('search_domains' in data) and (data['search_domains']):
                data['search_domains'] = data['search_domains'].split(',')

            if ip_ver == 4:
                cfg = IPConfig4(**data)
            else:
                cfg = IPConfig6(**data)

            self._ip_config[ip_ver] = cfg
            self._app.ui.body.update_ip_statuses()
            self._app.ui.body.remove_overlay()
        except (KeyError, ValueError) as exc:
            self._app.show_error_message(str(exc))

    def get_ip_config(self, ip_ver: int) -> dict[str, str]:
        if ip_ver not in (4, 6):
            raise ValueError(f'Unknown IP version {ip_ver}')
        return attrs.asdict(self._ip_config[ip_ver])

    def set_wifi_config(self, data: dict[str, str]):
        try:
            self._wifi_config = WIFIConfig(ssid=data['ssid'],
                                           psk=data['psk'])
            self._app.ui.body.update_wifi_status()
            self._app.ui.body.remove_overlay()
        except (KeyError, ValueError) as exc:
            self._app.show_error_message(str(exc))

    def get_wifi_config(self) -> Optional[dict[str, str]]:
        if self._wifi_config:
            return attrs.asdict(self._wifi_config)
        else:
            return None