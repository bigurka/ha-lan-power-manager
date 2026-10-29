"""Presence of a mapped device on the network: device_tracker.<device> home / not_home.

The tracker belongs to the HA device the integration creates for the mapped device
(when it has a MAC; without a MAC it is a standalone entity).
"""
from __future__ import annotations

from homeassistant.components.device_tracker import ScannerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LanPowerConfigEntry
from .entity import LanPowerEntity, async_get_ha_device
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

    async def async_internal_added_to_hass(self) -> None:
        """Link the tracker to our HA device, skipping ScannerEntity's own device logic.

        Since Home Assistant 2026 a ScannerEntity registers a device with its MAC and
        names it after the hostname (or the MAC): with the same MAC as our device that
        renamed it. The rest of the tracker setup still runs (super of ScannerEntity).
        """
        ha_device = async_get_ha_device(self.hass, self._manager.entry, self._device_id)
        if self.registry_entry is not None and ha_device is not None and self.mac_address:
            if self.registry_entry.device_id != ha_device.id:
                self.registry_entry = er.async_get(self.hass).async_update_entity(
                    self.entity_id, device_id=ha_device.id
                )
        await super(ScannerEntity, self).async_internal_added_to_hass()

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
