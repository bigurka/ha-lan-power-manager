"""Registers the LAN Power Manager sidebar panel (same approach as HACS and NeoPill)."""
from __future__ import annotations

import json
import pathlib

from homeassistant.components.frontend import async_register_built_in_panel, async_remove_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PANEL_ICON, PANEL_TITLE, PANEL_URL_PATH

_INTEGRATION_DIR = pathlib.Path(__file__).parent
_PANEL_DIST_DIR = _INTEGRATION_DIR / "panel_dist"
_WEBCOMPONENT_NAME = "lan-power-manager-panel"

_MANIFEST = json.loads((_INTEGRATION_DIR / "manifest.json").read_text(encoding="utf-8"))
_VERSION = _MANIFEST.get("version", "0")
# Version-scoped so a new release is never served from the browser cache.
_STATIC_URL_PATH = f"/api/{DOMAIN}/panel/{_VERSION}"
_STATIC_REGISTERED = f"{DOMAIN}_static_registered"


async def async_register_panel(hass: HomeAssistant) -> None:
    # Static paths cannot be unregistered: register once per HA run (entry reloads included).
    if not hass.data.get(_STATIC_REGISTERED):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_STATIC_URL_PATH, str(_PANEL_DIST_DIR), True)]
        )
        hass.data[_STATIC_REGISTERED] = True
    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL_PATH,
        config={
            "_panel_custom": {
                "name": _WEBCOMPONENT_NAME,
                "embed_iframe": False,
                "trust_external": False,
                "module_url": f"{_STATIC_URL_PATH}/entrypoint.js",
            }
        },
        require_admin=True,
    )


async def async_unregister_panel(hass: HomeAssistant) -> None:
    async_remove_panel(hass, PANEL_URL_PATH)
