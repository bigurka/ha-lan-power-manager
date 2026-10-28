"""Which entities a mapped device gets (pure functions, no Home Assistant objects)."""
from __future__ import annotations

from .const import (
    BUTTON_WOL,
    ENTITIES_BOTH,
    ENTITIES_CONTROL,
    ENTITIES_PRESENCE,
    OFF_ACTIONS,
    OFF_HIBERNATE,
    SHUTDOWN_NONE,
    SHUTDOWN_WINDOWS,
    SSH_OS_MACOS,
)
from .storage import Device


def has_presence(device: Device) -> bool:
    return device.mapped and device.entity_mode in (ENTITIES_PRESENCE, ENTITIES_BOTH)


def has_control(device: Device) -> bool:
    return device.mapped and device.entity_mode in (ENTITIES_CONTROL, ENTITIES_BOTH)


def button_kinds(device: Device) -> list[str]:
    """The buttons that make sense for this device."""
    if not has_control(device):
        return []
    kinds = [BUTTON_WOL] if device.mac and device.wol_enabled else []
    if device.shutdown_method != SHUTDOWN_NONE:
        target_os = None if device.shutdown_method == SHUTDOWN_WINDOWS else device.ssh_os
        kinds += [a for a in OFF_ACTIONS if not (a == OFF_HIBERNATE and target_os == SSH_OS_MACOS)]
    return kinds


def entities_signature(device: Device) -> tuple:
    """What decides the entities of a device: when it changes, the entry is reloaded."""
    return (device.mapped, device.entity_mode, device.off_action, tuple(button_kinds(device)), bool(device.mac))
