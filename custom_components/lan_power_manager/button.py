"""Buttons of a mapped computer: Wake-on-LAN, shutdown, hibernate, suspend.

Only the ones that make sense are created (no Wake-on-LAN without a MAC, no hibernate
on macOS, ...). entity_id button.<device>_<action>.
"""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LanPowerConfigEntry
from .const import BUTTON_WOL, DOMAIN
from .entity import LanPowerEntity
from .manager import NetworkManager
from .plan import button_kinds


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LanPowerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    manager = entry.runtime_data
    async_add_entities(
        PowerButton(manager, device.id, kind)
        for device in manager.store.mapped()
        for kind in button_kinds(device)
    )


class PowerButton(LanPowerEntity, ButtonEntity):
    def __init__(self, manager: NetworkManager, device_id: str, kind: str) -> None:
        super().__init__(manager, device_id, kind)
        self._kind = kind
        self._attr_translation_key = kind
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})
        self.entity_id = f"button.{self.object_id(manager.store.devices[device_id], kind)}"

    async def async_press(self) -> None:
        if self._kind == BUTTON_WOL:
            await self._manager.async_turn_on(self._device_id)
        else:
            await self._manager.async_turn_off(self._device_id, self._kind)
