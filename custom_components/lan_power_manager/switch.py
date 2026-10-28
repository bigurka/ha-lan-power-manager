"""The switch of a mapped computer: on = Wake-on-LAN, off = the device off action.

entity_id switch.<device>, stable when the off action changes; the action is in the
name ("<device> On / Hibernate") and in the off_action attribute.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LanPowerConfigEntry
from .const import DOMAIN
from .entity import LanPowerEntity
from .manager import NetworkManager
from .plan import has_control


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LanPowerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    manager = entry.runtime_data
    async_add_entities(PowerSwitch(manager, d.id) for d in manager.store.mapped() if has_control(d))


class PowerSwitch(LanPowerEntity, SwitchEntity):
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, manager: NetworkManager, device_id: str) -> None:
        super().__init__(manager, device_id, "power")
        device = manager.store.devices[device_id]
        self._off_action = device.off_action
        self._attr_translation_key = f"power_{device.off_action}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})
        self.entity_id = f"switch.{self.object_id(device)}"

    @property
    def is_on(self) -> bool | None:
        device = self.device
        return None if device is None else self._manager.is_on(device)

    @property
    def icon(self) -> str:
        device = self.device
        if device is not None and device.id in self._manager.pending:
            return "mdi:timer-sand"
        return "mdi:desktop-tower-monitor" if self.is_on else "mdi:desktop-tower"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        device = self.device
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
