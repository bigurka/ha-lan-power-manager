"""One switch per mapped computer: on = Wake-on-LAN, off = the device off action.

The off action (shutdown, hibernate, suspend) is part of the switch entity_id and
name, so it is clear what turning it off does. The lan_power_manager.shutdown /
hibernate / suspend / wake actions run any of them on a switch.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo, format_mac
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
    async_get_current_platform,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import LanPowerConfigEntry
from .const import (
    DOMAIN,
    OFF_ACTIONS,
    SIGNAL_DEVICE_MAPPED,
    SIGNAL_DEVICE_UNMAPPED,
    SIGNAL_DEVICES_UPDATED,
    SIGNAL_OFF_ACTION_CHANGED,
)
from .manager import NetworkManager, PowerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LanPowerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    manager = entry.runtime_data
    async_add_entities(PowerSwitch(manager, device.id) for device in manager.store.mapped())

    platform = async_get_current_platform()
    for action in OFF_ACTIONS:
        platform.async_register_entity_service(action, {}, f"async_{action}")
    platform.async_register_entity_service("wake", {}, "async_turn_on")

    @callback
    def _mapped(device_id: str) -> None:
        async_add_entities([PowerSwitch(manager, device_id)])

    @callback
    def _remove_switch(device_id: str, action: str) -> None:
        entity_registry = er.async_get(hass)
        if entity_id := entity_registry.async_get_entity_id("switch", DOMAIN, _unique_id(entry, device_id, action)):
            entity_registry.async_remove(entity_id)

    @callback
    def _off_action_changed(device_id: str, old_action: str) -> None:
        # New entity_id and name; the HA device (area, name) is kept.
        _remove_switch(device_id, old_action)
        async_add_entities([PowerSwitch(manager, device_id)])

    @callback
    def _unmapped(device_id: str) -> None:
        # Unmapping removes the switch and its HA device, not just makes it unavailable.
        _remove_switch(device_id, manager.store.devices[device_id].off_action)
        device_registry = dr.async_get(hass)
        if device := device_registry.async_get_device(identifiers={(DOMAIN, device_id)}):
            device_registry.async_update_device(device.id, remove_config_entry_id=entry.entry_id)

    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_DEVICE_MAPPED, _mapped))
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_DEVICE_UNMAPPED, _unmapped))
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_OFF_ACTION_CHANGED, _off_action_changed))

    # Clean up switches of devices unmapped (or whose off action changed) while Home
    # Assistant was not running, and those of older versions without the action.
    mapped_ids = {_unique_id(entry, d.id, d.off_action) for d in manager.store.mapped()}
    entity_registry = er.async_get(hass)
    for registry_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if registry_entry.domain == "switch" and registry_entry.unique_id not in mapped_ids:
            entity_registry.async_remove(registry_entry.entity_id)


def _unique_id(entry: LanPowerConfigEntry, device_id: str, action: str) -> str:
    return f"{entry.entry_id}_{device_id}_power_{action}"


class PowerSwitch(CoordinatorEntity[PowerCoordinator], SwitchEntity):
    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, manager: NetworkManager, device_id: str) -> None:
        super().__init__(manager.coordinator)
        self._manager = manager
        self._device_id = device_id
        device = manager.store.devices[device_id]
        self._off_action = device.off_action
        self._attr_unique_id = _unique_id(manager.entry, device_id, device.off_action)
        # Name "<device> On / Hibernate" in the HA language, entity_id always in English:
        # switch.<device>_hibernate. Only used the first time the switch is registered.
        self._attr_translation_key = f"power_{device.off_action}"
        self.entity_id = f"switch.{slugify(device.label)}_{device.off_action}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            connections={(CONNECTION_NETWORK_MAC, format_mac(device.mac))} if device.mac else set(),
            name=device.label,
            manufacturer=device.vendor,
            model="Windows PC" if device.windows else None,
        )

    @property
    def _device(self):
        return self._manager.store.devices.get(self._device_id)

    @property
    def available(self) -> bool:
        return super().available and self._device is not None and self._device.mapped

    @property
    def is_on(self) -> bool | None:
        device = self._device
        return None if device is None else self._manager.is_on(device)

    @property
    def icon(self) -> str:
        device = self._device
        if device is not None and device.id in self._manager.pending:
            return "mdi:timer-sand"
        return "mdi:desktop-tower-monitor" if self.is_on else "mdi:desktop-tower"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        device = self._device
        if device is None:
            return {}
        pending = self._manager.pending.get(device.id)
        return {
            "ip": device.ip,
            "mac": device.mac,
            "hostname": device.hostname,
            "online": device.online,
            "in_progress": None if pending is None else ("turning_on" if pending[0] else "turning_off"),
            "shutdown_method": device.shutdown_method,
            "off_action": self._off_action,
            "last_seen": device.last_seen,
            "last_action": device.last_action,
            "last_action_at": device.last_action_at,
            "last_action_ok": device.last_action_ok,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._manager.async_turn_on(self._device_id)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._manager.async_turn_off(self._device_id, self._off_action)

    async def async_shutdown(self) -> None:
        await self._manager.async_turn_off(self._device_id, "shutdown")

    async def async_hibernate(self) -> None:
        await self._manager.async_turn_off(self._device_id, "hibernate")

    async def async_suspend(self) -> None:
        await self._manager.async_turn_off(self._device_id, "suspend")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Keep the HA device name in sync when the label changes in the panel.
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_DEVICES_UPDATED, self._sync_device)
        )

    @callback
    def _sync_device(self) -> None:
        device = self._device
        if device is None or self.registry_entry is None or self.registry_entry.device_id is None:
            return
        device_registry = dr.async_get(self.hass)
        ha_device = device_registry.async_get(self.registry_entry.device_id)
        if ha_device is not None and ha_device.name != device.label:
            device_registry.async_update_device(ha_device.id, name=device.label)
        self.async_write_ha_state()
