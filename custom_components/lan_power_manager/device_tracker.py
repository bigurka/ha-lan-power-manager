"""Presence of a mapped device on the network: device_tracker.<device> home / not_home.

Home Assistant attaches a router tracker to its device through the MAC, so it shows
up on the device page when the MAC is known; without a MAC it is a standalone entity.
"""
from __future__ import annotations

from homeassistant.components.device_tracker import ScannerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LanPowerConfigEntry
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
    def __init__(self, manager: NetworkManager, device_id: str) -> None:
        super().__init__(manager, device_id, "tracker")
        device = manager.store.devices[device_id]
        if device.mac:
            # Named after its HA device, like the other entities.
            self._attr_name = None
        else:
            # No MAC, no HA device to attach to: carry the device name itself.
            self._attr_has_entity_name = False
            self._attr_name = device.label
        self.entity_id = f"device_tracker.{self.object_id(device)}"

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
