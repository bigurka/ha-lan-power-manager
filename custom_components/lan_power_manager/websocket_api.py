"""WebSocket API for the LAN Power Manager panel. Admin only: it controls the computers of the LAN."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    ENTITY_MODES,
    OFF_ACTIONS,
    POLICY_FORCE,
    POLICY_SKIP,
    SHUTDOWN_METHODS,
    SIGNAL_DEVICES_UPDATED,
    SSH_OSES,
)
from .network import normalize_mac

PREFIX = "lan_power_manager"


def _mac(value: Any) -> str | None:
    if value in (None, ""):
        return None
    mac = normalize_mac(str(value))
    if mac is None:
        raise vol.Invalid("invalid MAC address")
    return mac


def _optional_str(value: Any) -> str | None:
    value = "" if value is None else str(value).strip()
    return value or None


def _ip(value: Any) -> str | None:
    value = _optional_str(value)
    if value is None:
        return None
    import ipaddress  # noqa: PLC0415

    try:
        return str(ipaddress.IPv4Address(value))
    except ValueError as err:
        raise vol.Invalid("invalid IP address") from err


_OPTIONAL_INT = vol.Any(None, "", vol.All(vol.Coerce(int), vol.Range(min=0, max=3600)))

_DEVICE_FIELDS = {
    vol.Optional("mapped"): bool,
    vol.Optional("ignored"): bool,
    vol.Optional("name"): _optional_str,
    vol.Optional("mac"): _mac,
    vol.Optional("ip"): _ip,
    vol.Optional("wol_enabled"): bool,
    vol.Optional("broadcast"): _ip,
    vol.Optional("shutdown_method"): vol.In(SHUTDOWN_METHODS),
    vol.Optional("username"): _optional_str,
    vol.Optional("password"): vol.Any(None, str),
    vol.Optional("clear_password"): bool,
    vol.Optional("win_domain"): _optional_str,
    vol.Optional("ssh_port"): _OPTIONAL_INT,
    vol.Optional("ssh_command"): _optional_str,
    vol.Optional("ssh_os"): vol.In(SSH_OSES),
    vol.Optional("ssh_restricted"): bool,
    vol.Optional("forget_host_key"): bool,
    vol.Optional("off_action"): vol.In(OFF_ACTIONS),
    vol.Optional("entity_mode"): vol.In(ENTITY_MODES),
    vol.Optional("shutdown_delay"): _OPTIONAL_INT,
    vol.Optional("shutdown_message"): _optional_str,
    vol.Optional("user_policy"): vol.Any(None, "", vol.In([POLICY_FORCE, POLICY_SKIP])),
}


def async_setup_websocket_api(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_state)
    websocket_api.async_register_command(hass, ws_subscribe)
    websocket_api.async_register_command(hass, ws_scan)
    websocket_api.async_register_command(hass, ws_save_device)
    websocket_api.async_register_command(hass, ws_delete_device)
    websocket_api.async_register_command(hass, ws_power)
    websocket_api.async_register_command(hass, ws_ssh_setup)
    websocket_api.async_register_command(hass, ws_ssh_test)
    websocket_api.async_register_command(hass, ws_set_hide_rules)


def _manager(hass: HomeAssistant):
    from . import get_manager  # noqa: PLC0415

    return get_manager(hass)


def _clean(msg: dict[str, Any]) -> dict[str, Any]:
    changes = {k: v for k, v in msg.items() if k not in ("id", "type", "device_id")}
    for key in ("ssh_port", "shutdown_delay", "user_policy"):
        if changes.get(key) == "":
            changes[key] = None
    return changes


@websocket_api.websocket_command({vol.Required("type"): f"{PREFIX}/state"})
@websocket_api.require_admin
@callback
def ws_state(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        connection.send_result(msg["id"], _manager(hass).state_payload())
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_loaded", str(err))


@websocket_api.websocket_command({vol.Required("type"): f"{PREFIX}/subscribe"})
@websocket_api.require_admin
@callback
def ws_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Push the whole state to the panel whenever something changes (scan, poll, edit, action)."""

    @callback
    def _forward() -> None:
        try:
            payload = _manager(hass).state_payload()
        except HomeAssistantError:
            return
        connection.send_message(websocket_api.event_message(msg["id"], payload))

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(hass, SIGNAL_DEVICES_UPDATED, _forward)
    connection.send_result(msg["id"])
    _forward()


@websocket_api.websocket_command({vol.Required("type"): f"{PREFIX}/scan"})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_scan(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        manager = _manager(hass)
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_loaded", str(err))
        return
    # Answer at once: the panel follows progress through the subscription.
    hass.async_create_background_task(manager.async_scan(), "lan_power_manager panel scan")
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {vol.Required("type"): f"{PREFIX}/devices/save", vol.Optional("device_id"): str, **_DEVICE_FIELDS}
)
@websocket_api.require_admin
@callback
def ws_save_device(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        device = _manager(hass).async_save_device(msg.get("device_id"), _clean(msg))
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "save_failed", str(err))
        return
    connection.send_result(msg["id"], {"device": device.as_public_dict()})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{PREFIX}/devices/delete", vol.Required("device_id"): str}
)
@websocket_api.require_admin
@callback
def ws_delete_device(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        _manager(hass).async_delete_device(msg["device_id"])
    except HomeAssistantError as err:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, str(err))
        return
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{PREFIX}/devices/power",
        vol.Required("device_id"): str,
        vol.Required("on"): bool,
        # Off only: shutdown / hibernate / suspend instead of the device default.
        vol.Optional("action"): vol.In(OFF_ACTIONS),
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_power(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        manager = _manager(hass)
        if msg["on"]:
            detail = await manager.async_turn_on(msg["device_id"])
        else:
            detail = await manager.async_turn_off(msg["device_id"], msg.get("action"))
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "action_failed", str(err))
        return
    connection.send_result(msg["id"], {"detail": detail})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{PREFIX}/ssh/setup",
        vol.Optional("ssh_os"): vol.In(SSH_OSES),
        vol.Optional("ssh_restricted"): bool,
        vol.Optional("ssh_command"): _optional_str,
        vol.Optional("off_action"): vol.In(OFF_ACTIONS),
        vol.Optional("name"): _optional_str,
        vol.Optional("shutdown_delay"): _OPTIONAL_INT,
        vol.Optional("shutdown_message"): _optional_str,
    }
)
@websocket_api.require_admin
@callback
def ws_ssh_setup(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Home Assistant public key and the script that installs it on a PC."""
    try:
        result = _manager(hass).ssh_setup(_clean(msg))
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_loaded", str(err))
        return
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {vol.Required("type"): f"{PREFIX}/ssh/test", vol.Required("device_id"): str}
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_ssh_test(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        detail = await _manager(hass).async_ssh_test(msg["device_id"])
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "ssh_failed", str(err))
        return
    connection.send_result(msg["id"], {"detail": detail})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{PREFIX}/hide_rules/set",
        vol.Required("rules"): [vol.All(str, vol.Length(max=100))],
    }
)
@websocket_api.require_admin
@callback
def ws_set_hide_rules(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Texts that hide unmapped devices whose vendor, name or hostname contains them."""
    try:
        _manager(hass).async_set_hide_rules(msg["rules"])
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_loaded", str(err))
        return
    connection.send_result(msg["id"])
