"""Scan, inventory and power actions for one config entry.

The scan finds the hosts on the configured subnets, the coordinator keeps the online state of the
mapped devices fresh, and wake/shutdown are the switch actions.
"""
from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import timedelta
import ipaddress
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_PASSWORD,
    CONF_POLL_INTERVAL,
    CONF_SCAN_INTERVAL,
    CONF_SHUTDOWN_DELAY,
    CONF_SHUTDOWN_MESSAGE,
    CONF_SUBNETS,
    CONF_USER_POLICY,
    CONF_USERNAME,
    CONF_WIN_DOMAIN,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SHUTDOWN_DELAY,
    DEFAULT_SSH_COMMAND,
    DEFAULT_SSH_PORT,
    OFF_HIBERNATE,
    OFF_SHUTDOWN,
    SSH_KEY_COMMENT,
    SSH_KEY_STORAGE_KEY,
    SSH_OS_MACOS,
    SSH_OS_WINDOWS,
    STORAGE_VERSION,
    DOMAIN,
    EVENT_ACTION_RESULT,
    EVENT_NEW_DEVICE,
    PENDING_POLL_SECONDS,
    POLICY_FORCE,
    POLICY_SKIP,
    SHUTDOWN_NONE,
    SHUTDOWN_SSH,
    SHUTDOWN_TIMEOUT,
    SHUTDOWN_WINDOWS,
    SIGNAL_DEVICES_UPDATED,
    WAKE_TIMEOUT,
)
from .messages import Message, ha_language, translate
from .network import (
    Prober,
    async_load_vendors,
    async_netbios,
    async_reverse_dns,
    parse_subnets,
    read_arp_table,
    send_magic_packet,
    subnet_for,
    vendor_from_mac,
    wol_destinations,
)
from .plan import entities_signature
from .power import (
    ShutdownError,
    SshResult,
    SshTarget,
    WindowsCredentials,
    async_ssh_check,
    async_ssh_shutdown,
    generate_client_key,
    public_key_of,
    windows_power_off,
)
from .ssh_setup import off_command, setup_script
from .storage import Device, DeviceStore

_LOGGER = logging.getLogger(__name__)

_SCAN_CONCURRENCY = 64
_POLL_CONCURRENCY = 32


class PowerCoordinator(DataUpdateCoordinator[dict[str, bool]]):
    """Online state of the mapped devices, polled every few seconds."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, manager: NetworkManager) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=manager.setting(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)),
        )
        self._manager = manager

    async def _async_update_data(self) -> dict[str, bool]:
        return await self._manager.async_poll_mapped()


class NetworkManager:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, store: DeviceStore) -> None:
        self.hass = hass
        self.entry = entry
        self.store = store
        self._key_store: Store[dict[str, str]] = Store(hass, STORAGE_VERSION, SSH_KEY_STORAGE_KEY, private=True)
        self._ssh_private_key = ""
        self.ssh_public_key = ""
        self.ssh_key_fingerprint = ""
        self.prober = Prober(None)
        self.coordinator = PowerCoordinator(hass, entry, self)
        self.scanning = False
        self._scan_lock = asyncio.Lock()
        # device id -> (requested state, monotonic deadline) while a PC boots / shuts down
        self.pending: dict[str, tuple[bool, float]] = {}
        self._actions: set[asyncio.Task] = set()
        self._unsubs: list[CALLBACK_TYPE] = []

    # ---- settings ----

    def setting(self, key: str, default: Any = None) -> Any:
        # Once the options were saved they hold every setting (a cleared field is simply missing).
        value = (self.entry.options or self.entry.data).get(key)
        return default if value in (None, "") else value

    @property
    def subnets(self) -> list[ipaddress.IPv4Network]:
        try:
            return parse_subnets(self.setting(CONF_SUBNETS, ""))
        except ValueError:
            return []

    # ---- lifecycle ----

    async def async_setup(self) -> None:
        self.prober = Prober(await Prober.async_detect_icmp())
        await async_load_vendors()
        self._refresh_vendors()
        await self._async_load_ssh_key()
        if not self.prober.icmp_available:
            _LOGGER.info("ICMP not available: liveness is detected with TCP probes only")

        minutes = int(self.setting(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        if minutes > 0:
            self._unsubs.append(
                async_track_time_interval(
                    self.hass, self._async_scheduled_scan, timedelta(minutes=minutes), name=f"{DOMAIN} scan"
                )
            )
        await self.coordinator.async_config_entry_first_refresh()
        if self.store.is_empty:
            # First run: build the inventory right away so the panel is not empty.
            self.entry.async_create_background_task(self.hass, self.async_scan(), f"{DOMAIN} first scan")

    def _refresh_vendors(self) -> None:
        """Vendor names are derived from the MAC: recompute them with the full register."""
        changed = False
        for device in self.store.devices.values():
            vendor = vendor_from_mac(device.mac)
            if vendor and vendor != device.vendor:
                device.vendor = vendor
                changed = True
        if changed:
            self.store.async_schedule_save()

    async def async_unload(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        for task in list(self._actions):
            task.cancel()
        await self.store.async_save()

    async def _async_scheduled_scan(self, _now) -> None:
        await self.async_scan()

    # ---- scan ----

    async def async_scan(self) -> dict[str, int] | None:
        """Scan all subnets. Returns counters, or None if a scan was already running."""
        if self._scan_lock.locked():
            return None
        async with self._scan_lock:
            self.scanning = True
            self._notify()
            try:
                return await self._async_scan()
            finally:
                self.scanning = False
                self.store.last_scan = dt_util.utcnow().isoformat()
                self.store.async_schedule_save()
                self._notify()

    async def _async_scan(self) -> dict[str, int]:
        first_scan = self.store.is_empty
        now = dt_util.utcnow().isoformat()
        semaphore = asyncio.Semaphore(_SCAN_CONCURRENCY)
        found: dict[str, tuple[bool, str | None]] = {}  # ip -> (windows, netbios/dns name)
        netbios_macs: dict[str, str] = {}

        async def probe(ip: str) -> None:
            async with semaphore:
                online, windows = await self.prober.async_probe(ip, 0.7)
                if not online:
                    return
                name, mac = await async_netbios(ip) if windows else (None, None)
                if mac:
                    netbios_macs[ip] = mac
                name = await async_reverse_dns(ip) or name
                found[ip] = (windows, name)

        hosts = [str(h) for network in self.subnets for h in network.hosts()]
        await asyncio.gather(*(probe(ip) for ip in hosts))

        arp = await self.hass.async_add_executor_job(read_arp_table)
        new_devices: list[Device] = []
        seen: set[str] = set()
        for ip in sorted(found, key=lambda a: ipaddress.ip_address(a)):
            windows, name = found[ip]
            mac = arp.get(ip) or netbios_macs.get(ip)
            if mac:
                device = self.store.by_mac(mac) or self.store.by_ip_without_mac(ip)
            else:
                # No MAC from ARP/NetBIOS (e.g. behind a router): the IP is all we have.
                device = self.store.by_ip(ip)
            if device is None:
                device = self.store.add(Device(mac=mac, ip=ip, first_seen=now, new=not first_scan))
                new_devices.append(device)
            elif mac and device.mac is None:
                device.mac = mac
            if device.ip != ip and device.mapped:
                _LOGGER.info("%s changed IP: %s -> %s", device.label, device.ip, ip)
            device.ip = ip
            device.windows = device.windows or windows
            if name:
                device.hostname = name
            if device.vendor is None and device.mac:
                device.vendor = vendor_from_mac(device.mac)
            device.last_seen = now
            self._set_online(device, True)
            seen.add(device.id)

        # Online before and not seen now: a second, more patient probe before calling it off.
        missing = [d for d in self.store.devices.values() if d.online and d.id not in seen]
        offline = 0
        for device, (online, _) in zip(
            missing,
            await asyncio.gather(*(self._probe_device(d, 1.5) for d in missing)),
            strict=True,
        ):
            if online:
                device.last_seen = now
            else:
                self._set_online(device, False)
                offline += 1

        for device in new_devices:
            if device.new:
                self.hass.bus.async_fire(
                    EVENT_NEW_DEVICE,
                    {"device_id": device.id, "ip": device.ip, "mac": device.mac,
                     "hostname": device.hostname, "vendor": device.vendor},
                )
        await self.coordinator.async_request_refresh()
        result = {"hosts": len(hosts), "online": len(seen), "new": len(new_devices), "offline": offline}
        _LOGGER.debug("Scan finished: %s", result)
        return result

    async def _probe_device(self, device: Device, timeout: float) -> tuple[bool, bool]:
        if not device.ip:
            return False, False
        return await self.prober.async_probe(device.ip, timeout)

    def _set_online(self, device: Device, online: bool) -> None:
        if device.online != online or device.last_change is None:
            device.online = online
            device.last_change = dt_util.utcnow().isoformat()

    # ---- polling (coordinator) ----

    async def async_poll_mapped(self) -> dict[str, bool]:
        devices = self.store.mapped()
        semaphore = asyncio.Semaphore(_POLL_CONCURRENCY)

        async def probe(device: Device) -> bool:
            async with semaphore:
                online, _ = await self._probe_device(device, 0.8)
                # A single lost ping is not a shutdown: try again with more patience.
                if not online and device.online:
                    online, _ = await self._probe_device(device, 1.5)
                return online

        results = await asyncio.gather(*(probe(d) for d in devices))
        now = dt_util.utcnow().isoformat()
        changed = False
        for device, online in zip(devices, results, strict=True):
            if online:
                device.last_seen = now
            if device.online != online:
                self._set_online(device, online)
                changed = True
            pending = self.pending.get(device.id)
            if pending and (pending[0] == online or time.monotonic() > pending[1]):
                self.pending.pop(device.id, None)
        if changed:
            self.store.async_schedule_save()
            self._notify()
        return {d.id: d.online for d in devices}

    # ---- power ----

    def is_on(self, device: Device) -> bool:
        pending = self.pending.get(device.id)
        if pending and time.monotonic() <= pending[1]:
            return pending[0]
        return device.online

    async def async_turn_on(self, device_id: str) -> str:
        """Send the Wake-on-LAN packet. Returns what happened, for the panel."""
        device = self._get(device_id)
        if not device.wol_enabled:
            raise self._error("wol_disabled", name=device.label)
        if not device.mac:
            raise self._error("no_mac", name=device.label)
        if (await self._probe_device(device, 1.0))[0]:
            self._set_online(device, True)
            return self._record(device, "on", True, Message("already_on"))
        destinations = wol_destinations(device.ip, subnet_for(device.ip, self.subnets), device.broadcast)
        await self.hass.async_add_executor_job(send_magic_packet, device.mac, destinations)
        detail = self._record(
            device, "on", True, Message("wol_sent", {"mac": device.mac, "destinations": ", ".join(destinations)})
        )
        self._start_pending(device, True, WAKE_TIMEOUT)
        return detail

    async def async_turn_off(self, device_id: str, action: str | None = None) -> str:
        """Shut down, hibernate or suspend the computer (default: the device off action).

        Returns what happened, for the panel.
        """
        device = self._get(device_id)
        action = action or device.off_action
        method = device.shutdown_method
        if method == SHUTDOWN_NONE:
            raise self._error("no_shutdown_method", name=device.label)
        if not device.ip:
            raise self._error("no_ip", name=device.label)
        if await self._is_local_address(device.ip):
            # Never switch off the machine Home Assistant runs on.
            raise self._error("is_ha_host", name=device.label)
        if not (await self._probe_device(device, 1.0))[0]:
            self._set_online(device, False)
            return self._record(device, "off", True, Message("already_off"))

        action_name = Message(f"action_{action}")
        try:
            command = self.off_command(device, action)
            if method == SHUTDOWN_WINDOWS:
                user = await self._async_windows_power_off(device, command)
                warned = action == OFF_SHUTDOWN and self._delay(device) > 0
                outcome = Message(
                    "wmi_sent",
                    {
                        "action": action_name,
                        "when": Message("in_seconds", {"delay": self._delay(device)}) if warned else "",
                        "user": Message("user_logged_on", {"user": user}) if user else "",
                    },
                )
            else:
                if device.ssh_restricted and action != device.off_action:
                    raise ShutdownError(
                        "ssh_restricted_other",
                        name=device.label,
                        default=Message(f"action_{device.off_action}"),
                        action=action_name,
                    )
                result = await async_ssh_shutdown(self._ssh_target(device), command)
                self._remember_host_key(device, result)
                outcome = Message(result.detail.key, {"action": action_name})
        except ShutdownError as err:
            raise HomeAssistantError(self._record(device, "off", False, err.message)) from err

        detail = self._record(device, "off", True, outcome)
        warning = self._delay(device) if action == OFF_SHUTDOWN and self._target_os(device) == SSH_OS_WINDOWS else 0
        self._start_pending(device, False, SHUTDOWN_TIMEOUT + warning, action)
        return detail

    def _target_os(self, device: Device) -> str:
        return SSH_OS_WINDOWS if device.shutdown_method == SHUTDOWN_WINDOWS else device.ssh_os

    def off_command(self, device: Device, action: str) -> str:
        """The command that performs an off action on this device."""
        # A custom SSH command replaces the command of the device default action only.
        if device.shutdown_method == SHUTDOWN_SSH and device.ssh_command and action == device.off_action:
            return device.ssh_command
        command = off_command(self._target_os(device), action, self._delay(device), self._message(device))
        if command is None:
            raise ShutdownError("action_not_supported", name=device.label, action=Message(f"action_{action}"))
        return command

    async def _async_windows_power_off(self, device: Device, command: str) -> str | None:
        username = device.username or self.setting(CONF_USERNAME, "")
        if not username:
            raise ShutdownError("missing_windows_credentials")
        credentials = WindowsCredentials(
            username=username,
            password=device.password or self.setting(CONF_PASSWORD, ""),
            domain=device.win_domain or self.setting(CONF_WIN_DOMAIN, ""),
        )
        policy = device.user_policy or self.setting(CONF_USER_POLICY, POLICY_FORCE)
        return await self.hass.async_add_executor_job(
            windows_power_off, device.ip, credentials, command, policy == POLICY_SKIP
        )

    # ---- SSH ----

    async def _async_load_ssh_key(self) -> None:
        """Load Home Assistant's own SSH key pair, generating it the first time."""
        data = await self._key_store.async_load() or {}
        if not data.get("private_key"):
            private_key = await self.hass.async_add_executor_job(generate_client_key, SSH_KEY_COMMENT)
            data = {"private_key": private_key}
            await self._key_store.async_save(data)
            _LOGGER.info("Generated the Home Assistant SSH key")
        self._ssh_private_key = data["private_key"]
        self.ssh_public_key, self.ssh_key_fingerprint = await self.hass.async_add_executor_job(
            public_key_of, self._ssh_private_key
        )

    def _ssh_target(self, device: Device) -> SshTarget:
        username = device.username or self.setting(CONF_USERNAME, "")
        if not username:
            raise ShutdownError("missing_ssh_user")
        return SshTarget(
            ip=device.ip,
            port=int(device.ssh_port or DEFAULT_SSH_PORT),
            username=username,
            password=device.password or self.setting(CONF_PASSWORD, "") or None,
            client_key=self._ssh_private_key,
            host_key=device.ssh_host_key,
        )

    def _message(self, device: Device) -> str:
        return device.shutdown_message or self.default_message


    def _remember_host_key(self, device: Device, result: SshResult) -> None:
        if result.learned_host_key and not device.ssh_host_key:
            device.ssh_host_key = result.learned_host_key
            device.ssh_host_fingerprint = result.learned_fingerprint
            self.store.async_schedule_save()
            self._notify()

    async def async_ssh_test(self, device_id: str) -> str:
        """Check login with the Home Assistant key (and pin the PC identity) without running anything."""
        device = self._get(device_id)
        if not device.ip:
            raise self._error("no_ip", name=device.label)
        try:
            result = await async_ssh_check(self._ssh_target(device))
        except ShutdownError as err:
            raise HomeAssistantError(err.message.text(self.language)) from err
        self._remember_host_key(device, result)
        return result.detail.text(self.language)

    def ssh_setup(self, params: dict[str, Any]) -> dict[str, str]:
        """Public key and setup script for the values currently in the panel dialog."""
        probe = Device(
            name=params.get("name") or None,
            shutdown_method=SHUTDOWN_SSH,
            ssh_os=params.get("ssh_os") or SSH_OS_WINDOWS,
            ssh_command=params.get("ssh_command") or None,
            off_action=params.get("off_action") or OFF_SHUTDOWN,
            shutdown_delay=params.get("shutdown_delay"),
            shutdown_message=params.get("shutdown_message") or None,
        )
        restricted = bool(params.get("ssh_restricted"))
        try:
            command = self.off_command(probe, probe.off_action)
        except ShutdownError as err:
            raise HomeAssistantError(err.message.text(self.language)) from err
        return {
            "public_key": self.ssh_public_key,
            "fingerprint": self.ssh_key_fingerprint,
            "command": command,
            "script": setup_script(probe.ssh_os, self.ssh_public_key, restricted, command),
        }

    def _delay(self, device: Device) -> int:
        if device.shutdown_delay is not None:
            return int(device.shutdown_delay)
        return int(self.setting(CONF_SHUTDOWN_DELAY, DEFAULT_SHUTDOWN_DELAY))

    async def _is_local_address(self, ip: str) -> bool:
        from homeassistant.components import network  # noqa: PLC0415

        if ipaddress.ip_address(ip).is_loopback:
            return True
        adapters = await network.async_get_adapters(self.hass)
        return any(a["address"] == ip for adapter in adapters for a in adapter["ipv4"])

    def _start_pending(self, device: Device, state: bool, timeout: int, action: str | None = None) -> None:
        self.pending[device.id] = (state, time.monotonic() + timeout)
        self.coordinator.async_update_listeners()
        task = self.entry.async_create_background_task(
            self.hass, self._async_follow(device.id, state, timeout, action), f"{DOMAIN} follow {device.id}"
        )
        self._actions.add(task)
        task.add_done_callback(self._actions.discard)

    async def _async_follow(self, device_id: str, state: bool, timeout: int, action: str | None) -> None:
        """Poll quickly until the PC reaches the requested state, then report the outcome."""
        deadline = time.monotonic() + timeout
        reached = False
        while not reached and time.monotonic() < deadline:
            await asyncio.sleep(PENDING_POLL_SECONDS)
            device = self.store.devices.get(device_id)
            if device is None or self.pending.get(device_id, (None,))[0] != state:
                return  # removed, or superseded by another action
            online, _ = await self._probe_device(device, 1.0)
            reached = online == state
        device = self.store.devices.get(device_id)
        self.pending.pop(device_id, None)
        if device is None:
            return
        if reached:
            self._set_online(device, state)
            if state:
                device.last_seen = dt_util.utcnow().isoformat()
        self.coordinator.async_set_updated_data({d.id: d.online for d in self.store.mapped()})
        if reached:
            outcome = Message("turned_on" if state else "turned_off")
        elif state:
            outcome = Message("wake_failed")
        else:
            outcome = Message("off_failed", {"action": Message(f"action_{action or OFF_SHUTDOWN}")})
        self._record(device, "on" if state else "off", reached, outcome)

    @property
    def language(self) -> str:
        return ha_language(self.hass)

    @property
    def default_message(self) -> str:
        return self.setting(CONF_SHUTDOWN_MESSAGE) or translate(self.language, "default_shutdown_message")

    def _error(self, key: str, **placeholders: Any) -> HomeAssistantError:
        return HomeAssistantError(translate(self.language, key, **placeholders))

    def _record(self, device: Device, action: str, ok: bool, message: Message) -> str:
        """Store and announce the outcome of an action; returns its text."""
        detail = message.text(self.language)
        log = _LOGGER.info if ok else _LOGGER.warning
        log("%s %s: %s", device.label, action, detail)
        device.last_action = detail
        device.last_action_at = dt_util.utcnow().isoformat()
        device.last_action_ok = ok
        self.store.async_schedule_save()
        self.hass.bus.async_fire(
            EVENT_ACTION_RESULT,
            {
                "device_id": device.id,
                "name": device.label,
                "action": action,
                "success": ok,
                # Language independent, for automations; "detail" is the text in the HA language.
                "result": message.key,
                "detail": detail,
            },
        )
        self._notify()
        return detail

    # ---- inventory edits (panel) ----

    def _get(self, device_id: str) -> Device:
        device = self.store.devices.get(device_id)
        if device is None:
            raise self._error("device_not_found", device_id=device_id)
        return device

    @callback
    def async_save_device(self, device_id: str | None, changes: dict[str, Any]) -> Device:
        existing = None if device_id is None else self._get(device_id)
        mac = changes.get("mac", existing.mac if existing else None)
        if mac and (other := self.store.by_mac(mac)) is not None and other is not existing:
            raise self._error("mac_in_use", mac=mac, other=other.label)
        clear_password = changes.pop("clear_password", False)
        forget_host_key = changes.pop("forget_host_key", False)
        if "password" in changes and changes["password"] in (None, ""):
            changes.pop("password")  # blank = keep the stored one
        result = replace(existing or Device(), **changes)
        if self._target_os(result) == SSH_OS_MACOS and result.off_action == OFF_HIBERNATE:
            raise self._error("action_not_supported", name=result.label, action=Message("action_hibernate"))

        device = existing or self.store.add(Device(first_seen=dt_util.utcnow().isoformat(), new=False))
        before = entities_signature(device)
        if clear_password:
            device.password = None
        if forget_host_key:
            device.ssh_host_key = device.ssh_host_fingerprint = None
        for key, value in changes.items():
            setattr(device, key, value)
        if device.mac and device.vendor is None:
            device.vendor = vendor_from_mac(device.mac)
        if device.mapped:
            device.ignored = False
            device.new = False
        self.store.async_schedule_save()

        if entities_signature(device) != before:
            self._async_rebuild_entities()
        else:
            self.coordinator.async_update_listeners()
        self._notify()
        return device

    @callback
    def async_delete_device(self, device_id: str) -> None:
        device = self._get(device_id)
        self.store.remove(device_id)
        self.pending.pop(device_id, None)
        self.store.async_schedule_save()
        if device.mapped:
            self._async_rebuild_entities()
        self._notify()

    @callback
    def _async_rebuild_entities(self) -> None:
        """Entities to add or remove (mapping, entity mode, off action, ...): reload the entry,
        which creates exactly the expected entities and removes the others."""
        self.hass.config_entries.async_schedule_reload(self.entry.entry_id)

    @callback
    def _notify(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_DEVICES_UPDATED)

    def state_payload(self) -> dict[str, Any]:
        return {
            "devices": [
                {**d.as_public_dict(), "pending": self.pending[d.id][0] if d.id in self.pending else None}
                for d in self.store.devices.values()
            ],
            "scanning": self.scanning,
            "last_scan": self.store.last_scan,
            "ssh_public_key": self.ssh_public_key,
            "ssh_key_fingerprint": self.ssh_key_fingerprint,
            "subnets": [str(s) for s in self.subnets],
            "defaults": {
                "username": self.setting(CONF_USERNAME, ""),
                "shutdown_delay": int(self.setting(CONF_SHUTDOWN_DELAY, DEFAULT_SHUTDOWN_DELAY)),
                "shutdown_message": self.default_message,
                "user_policy": self.setting(CONF_USER_POLICY, POLICY_FORCE),
                "ssh_port": DEFAULT_SSH_PORT,
                "ssh_command": DEFAULT_SSH_COMMAND,
            },
        }

