"""Which entities each mapped device gets, the Home Assistant devices behind them,
and the base class shared by the switch, the buttons and the device tracker.

The set of entities follows the device settings in the panel (entity mode, off action,
shutdown method, MAC). Whenever one of those changes the config entry is reloaded and
everything here is rebuilt, so the platforms never have to add or remove entities live.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import DOMAIN
from .manager import NetworkManager, PowerCoordinator
from .plan import button_kinds, has_control, has_presence
from .storage import Device

HUB_IDENTIFIER = (DOMAIN, "hub")


def unique_id(entry: ConfigEntry, device_id: str, kind: str) -> str:
    return f"{entry.entry_id}_{device_id}_{kind}"


def expected_unique_ids(entry: ConfigEntry, manager: NetworkManager) -> set[str]:
    ids: set[str] = set()
    for device in manager.store.mapped():
        if has_presence(device):
            ids.add(unique_id(entry, device.id, "tracker"))
        if has_control(device):
            ids.add(unique_id(entry, device.id, "power"))
        ids.update(unique_id(entry, device.id, kind) for kind in button_kinds(device))
    return ids


@callback
def async_sync_registries(hass: HomeAssistant, entry: ConfigEntry, manager: NetworkManager) -> None:
    """Create the HA device of every mapped device, remove what is no longer wanted.

    The devices are created here (not by the entities) because a device tracker can
    only attach to an existing device with its MAC, also when it is the only entity.
    """
    device_registry = dr.async_get(hass)
    mapped = {d.id: d for d in manager.store.mapped()}
    for device in mapped.values():
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, device.id)},
            connections={(dr.CONNECTION_NETWORK_MAC, dr.format_mac(device.mac))} if device.mac else set(),
            name=device.label,
            manufacturer=device.vendor,
            model="Windows PC" if device.windows else None,
        )

    entity_registry = er.async_get(hass)
    expected = expected_unique_ids(entry, manager)
    for registry_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if registry_entry.unique_id not in expected:
            entity_registry.async_remove(registry_entry.entity_id)

    for ha_device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        ours = {i[1] for i in ha_device.identifiers if i[0] == DOMAIN}
        if HUB_IDENTIFIER[1] in ours or ours & mapped.keys():
            continue
        if _devices_per_entry(device_registry):
            # Home Assistant 2026+: a device belongs to a single config entry.
            device_registry.async_remove_device(ha_device.id)
        else:
            # Older versions: the device may be shared with other integrations.
            device_registry.async_update_device(ha_device.id, remove_config_entry_id=entry.entry_id)


def _devices_per_entry(registry: dr.DeviceRegistry) -> bool:
    """True on Home Assistant versions where each device belongs to one config entry."""
    return hasattr(registry, "async_get_device_by_identifier")


@callback
def async_get_ha_device(hass: HomeAssistant, entry: ConfigEntry, device_id: str) -> dr.DeviceEntry | None:
    """The HA device of a mapped device.

    Home Assistant 2026.x looks devices up per config entry (identifiers are no longer
    unique across entries); older versions only have the global lookup.
    """
    registry = dr.async_get(hass)
    identifier = (DOMAIN, device_id)
    if _devices_per_entry(registry):
        return registry.async_get_device_by_identifier(identifier, entry.entry_id)
    return registry.async_get_device(identifiers={identifier})


@callback
def async_sync_device_names(hass: HomeAssistant, manager: NetworkManager) -> None:
    """Keep the HA device names in line with the labels edited in the panel."""
    device_registry = dr.async_get(hass)
    for device in manager.store.mapped():
        ha_device = async_get_ha_device(hass, manager.entry, device.id)
        if ha_device is not None and ha_device.name != device.label:
            device_registry.async_update_device(ha_device.id, name=device.label)


class LanPowerEntity(CoordinatorEntity[PowerCoordinator]):
    """An entity of one mapped device."""

    _attr_has_entity_name = True

    def __init__(self, manager: NetworkManager, device_id: str, kind: str) -> None:
        super().__init__(manager.coordinator)
        self._manager = manager
        self._device_id = device_id
        self._attr_unique_id = unique_id(manager.entry, device_id, kind)

    @property
    def device(self) -> Device | None:
        return self._manager.store.devices.get(self._device_id)

    @property
    def available(self) -> bool:
        return super().available and self.device is not None and self.device.mapped

    @staticmethod
    def object_id(device: Device, suffix: str | None = None) -> str:
        """English, stable object id: <device>[_<suffix>]. Used only at first registration."""
        base = slugify(device.label)
        return f"{base}_{suffix}" if suffix else base
