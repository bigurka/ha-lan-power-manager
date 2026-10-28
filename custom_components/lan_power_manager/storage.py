"""Persistent inventory of the devices seen on the network.

A device is identified by its MAC: when DHCP gives it another IP it stays the same
device. Devices that go offline stay in the list with their last IP and last seen.
Only the ones the user maps in the panel get a switch.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any
import uuid

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    ENTITIES_CONTROL,
    OFF_SHUTDOWN,
    SHUTDOWN_NONE,
    SSH_OS_WINDOWS,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .network import is_random_mac

_SAVE_DELAY = 5

# Never sent to the panel: the panel only learns whether a password is set.
SECRET_FIELDS = ("password",)


@dataclass(slots=True)
class Device:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    mac: str | None = None
    ip: str | None = None
    hostname: str | None = None
    vendor: str | None = None
    windows: bool = False
    online: bool = False
    first_seen: str | None = None
    last_seen: str | None = None
    last_change: str | None = None
    ignored: bool = False
    new: bool = True

    # Set when the user maps the device in the panel: only mapped devices get entities.
    mapped: bool = False
    # Which ones: presence (device_tracker), control (switch + buttons) or both.
    # Devices mapped before this setting existed had only the switch.
    entity_mode: str = ENTITIES_CONTROL
    name: str | None = None
    wol_enabled: bool = True
    broadcast: str | None = None
    shutdown_method: str = SHUTDOWN_NONE
    # What the switch does when turned off: shutdown, hibernate or suspend.
    off_action: str = OFF_SHUTDOWN
    # Empty = use the credentials of the integration options.
    username: str | None = None
    password: str | None = None
    win_domain: str | None = None
    ssh_port: int | None = None
    ssh_command: str | None = None
    ssh_os: str = SSH_OS_WINDOWS
    # The key installed on the PC only allows the shutdown (forced command).
    ssh_restricted: bool = False
    # Host key of the PC, remembered at the first connection: a different key is refused.
    ssh_host_key: str | None = None
    ssh_host_fingerprint: str | None = None
    # None = use the integration defaults.
    shutdown_delay: int | None = None
    shutdown_message: str | None = None
    user_policy: str | None = None

    last_action: str | None = None
    last_action_at: str | None = None
    last_action_ok: bool | None = None

    @property
    def label(self) -> str:
        return self.name or self.hostname or self.ip or self.mac or self.id[:8]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Device:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_public_dict(self) -> dict[str, Any]:
        data = self.as_dict()
        for key in SECRET_FIELDS:
            data[f"has_{key}"] = bool(data.pop(key))
        data["label"] = self.label
        data["random_mac"] = is_random_mac(self.mac)
        return data


class DeviceStore:
    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY, private=True)
        self.devices: dict[str, Device] = {}
        self.last_scan: str | None = None
        # Texts (e.g. "shelly", "espressif"): unmapped devices whose vendor, name or
        # hostname contains one are hidden from the list and raise no new-device event.
        self.hide_rules: list[str] = []

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.devices = {d["id"]: Device.from_dict(d) for d in data.get("devices", [])}
        self.last_scan = data.get("last_scan")
        self.hide_rules = list(data.get("hide_rules", []))

    def _data(self) -> dict[str, Any]:
        return {
            "devices": [d.as_dict() for d in self.devices.values()],
            "last_scan": self.last_scan,
            "hide_rules": self.hide_rules,
        }

    def hidden_by(self, device: Device) -> str | None:
        """The hide rule that matches the device, if any. Mapped devices are never hidden."""
        if device.mapped:
            return None
        haystack = " ".join(filter(None, (device.vendor, device.hostname, device.name))).lower()
        return next((rule for rule in self.hide_rules if rule.lower() in haystack), None)

    def async_schedule_save(self) -> None:
        self._store.async_delay_save(self._data, _SAVE_DELAY)

    async def async_save(self) -> None:
        await self._store.async_save(self._data())

    def by_mac(self, mac: str | None) -> Device | None:
        if mac is None:
            return None
        return next((d for d in self.devices.values() if d.mac == mac), None)

    def by_ip_without_mac(self, ip: str) -> Device | None:
        return next((d for d in self.devices.values() if d.mac is None and d.ip == ip), None)

    def by_ip(self, ip: str) -> Device | None:
        matches = [d for d in self.devices.values() if d.ip == ip]
        # Prefer the device the user cares about.
        return next((d for d in matches if d.mapped), None) or next(iter(matches), None)

    def mapped(self) -> list[Device]:
        return [d for d in self.devices.values() if d.mapped]

    @property
    def is_empty(self) -> bool:
        return not self.devices

    def add(self, device: Device) -> Device:
        self.devices[device.id] = device
        return device

    def remove(self, device_id: str) -> Device | None:
        return self.devices.pop(device_id, None)

