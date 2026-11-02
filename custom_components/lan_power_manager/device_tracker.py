"""Presence of a mapped device on the network: device_tracker.<device> home / not_home.

The tracker declares the HA device the integration creates for the mapped device
(with its MAC as a connection), as Home Assistant asks of ScannerEntity trackers since
2026.11. Without it Home Assistant would make up a device named after the hostname,
renaming ours.
"""
from __future__ import annotations

from homeassistant.components.device_tracker import ScannerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo, format_mac
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LanPowerConfigEntry
from .const import DOMAIN
from .entity import LanPowerEntity
from .manager import NetworkManager
from .plan import has_presence


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LanPowerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    manager = entry.runtime_data
    async_add_entities(PresenceTracker(manager, d.id) for d in manager.store.mapped() if has_presence(d))


class PresenceTracker(LanPowerEntity, ScannerEntity):
    # Named after its HA device, like the other entities.
    _attr_name = None

    def __init__(self, manager: NetworkManager, device_id: str) -> None:
        super().__init__(manager, device_id, "tracker")
        device = manager.store.devices[device_id]
        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            connections={(CONNECTION_NETWORK_MAC, format_mac(device.mac))} if device.mac else set(),
        )
        self.entity_id = f"device_tracker.{self.object_id(device)}"

    @property
    def device_info(self) -> DeviceInfo:
        # A property, not _attr_device_info: before 2026.11 ScannerEntity had its own
        # device_info property that always returned None.
        return self._device_info

    @property
    def entity_registry_enabled_default(self) -> bool:
        # Since 2026.11 trackers start disabled; this one was asked for in the panel.
        return True

    @property
    def unique_id(self) -> str | None:
        return self._attr_unique_id

    @property
    def is_connected(self) -> bool:
        device = self.device
        return bool(device and device.online)

    @property
    def mac_address(self) -> str | None:
        device = self.device
        return format_mac(device.mac) if device and device.mac else None

    @property
    def ip_address(self) -> str | None:
        device = self.device
        return device.ip if device else None

    @property
    def hostname(self) -> str | None:
        device = self.device
        return device.hostname if device else None
