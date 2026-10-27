"""LAN Power Manager: network scan and power control of the LAN computers."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import config_validation as cv, device_registry as dr

from .const import DOMAIN, PANEL_URL_PATH
from .manager import NetworkManager
from .panel import async_register_panel, async_unregister_panel
from .storage import DeviceStore
from .websocket_api import async_setup_websocket_api

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SWITCH]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type LanPowerConfigEntry = ConfigEntry[NetworkManager]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the websocket API and the scan action once, regardless of config entries."""
    async_setup_websocket_api(hass)

    async def _scan(call: ServiceCall) -> dict:
        manager = get_manager(hass)
        result = await manager.async_scan()
        return result or {"already_running": True}

    hass.services.async_register(
        DOMAIN, "scan", _scan, supports_response=SupportsResponse.OPTIONAL
    )
    return True


def get_manager(hass: HomeAssistant) -> NetworkManager:
    from homeassistant.exceptions import HomeAssistantError  # noqa: PLC0415

    from .messages import ha_language, translate  # noqa: PLC0415

    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    if not entries:
        raise HomeAssistantError(translate(ha_language(hass), "not_configured"))
    return entries[0].runtime_data


async def async_setup_entry(hass: HomeAssistant, entry: LanPowerConfigEntry) -> bool:
    store = DeviceStore(hass)
    await store.async_load()

    manager = NetworkManager(hass, entry, store)
    entry.runtime_data = manager
    await manager.async_setup()

    await async_register_panel(hass)
    _async_register_hub_device(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


def _async_register_hub_device(hass: HomeAssistant, entry: LanPowerConfigEntry) -> None:
    """A service device on the integration page whose link opens the LAN Power panel."""
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "hub")},
        name="LAN Power Manager",
        manufacturer="LAN Power Manager",
        model="LAN Power panel",
        entry_type=dr.DeviceEntryType.SERVICE,
        configuration_url=f"homeassistant://{PANEL_URL_PATH}",
    )


async def _async_options_updated(hass: HomeAssistant, entry: LanPowerConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: LanPowerConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_unload()
        await async_unregister_panel(hass)
    return unload_ok
