"""Network probes used by the scan and by the power switches.

Everything runs with the privileges Home Assistant already has: TCP connects, ICMP
through icmplib (when the system allows it), the kernel ARP table, NetBIOS and
reverse DNS.
"""
from __future__ import annotations

import asyncio
import contextlib
import errno
import ipaddress
import logging
import re
import socket

_LOGGER = logging.getLogger(__name__)

# 135/445 answer only on Windows; the others catch Linux, NAS, printers, ...
WINDOWS_PORTS = (135, 445)
OTHER_PORTS = (3389, 22, 80, 443, 139)

WOL_PORTS = (9, 7)

_MAC_RE = re.compile(r"^([0-9a-f]{2})[:\-.]?([0-9a-f]{2})[:\-.]?([0-9a-f]{2})[:\-.]?"
                     r"([0-9a-f]{2})[:\-.]?([0-9a-f]{2})[:\-.]?([0-9a-f]{2})$", re.IGNORECASE)

# Only prefixes we are sure of: a wrong vendor is worse than none.
_OUI = {
    "000C29": "VMware", "005056": "VMware", "000569": "VMware",
    "00155D": "Microsoft Hyper-V", "080027": "VirtualBox", "525400": "QEMU/KVM",
    "B827EB": "Raspberry Pi", "DCA632": "Raspberry Pi", "E45F01": "Raspberry Pi", "D83ADD": "Raspberry Pi",
    "2CCF67": "Raspberry Pi", "001132": "Synology",
    "24A43C": "Ubiquiti", "788A20": "Ubiquiti", "FCECDA": "Ubiquiti", "802AA8": "Ubiquiti",
    "00000C": "Cisco",
}


def normalize_mac(value: str | None) -> str | None:
    """Return the MAC as AA:BB:CC:DD:EE:FF, or None if it is not a valid unicast MAC."""
    if not value:
        return None
    match = _MAC_RE.match(value.strip())
    if not match:
        return None
    mac = ":".join(g.upper() for g in match.groups())
    if mac in ("00:00:00:00:00:00", "FF:FF:FF:FF:FF:FF"):
        return None
    return mac


def vendor_from_mac(mac: str | None) -> str | None:
    mac = normalize_mac(mac)
    if mac is None:
        return None
    prefix = mac.replace(":", "")[:6]
    return _OUI.get(prefix)


def is_random_mac(mac: str | None) -> bool:
    """Locally administered bit set: a random (phones) or virtual address, no vendor."""
    mac = normalize_mac(mac)
    return mac is not None and bool(int(mac[:2], 16) & 0x02)


def parse_subnets(text: str) -> list[ipaddress.IPv4Network]:
    """Parse a comma/space separated list of IPv4 CIDRs. Raises ValueError."""
    networks = []
    for part in re.split(r"[,\s;]+", text.strip()):
        if not part:
            continue
        network = ipaddress.ip_network(part, strict=False)
        if not isinstance(network, ipaddress.IPv4Network):
            raise ValueError(f"{part}: solo IPv4")
        networks.append(network)
    return networks


def subnet_for(ip: str | None, subnets: list[ipaddress.IPv4Network]) -> ipaddress.IPv4Network | None:
    with contextlib.suppress(ValueError, TypeError):
        address = ipaddress.ip_address(ip)
        for network in subnets:
            if address in network:
                return network
    return None


class Prober:
    """Liveness probe: ping or any TCP answer (even a refused connection) means alive."""

    def __init__(self, icmp_privileged: bool | None) -> None:
        # None = ICMP not usable here, TCP only.
        self._icmp_privileged = icmp_privileged

    @property
    def icmp_available(self) -> bool:
        return self._icmp_privileged is not None

    @staticmethod
    async def async_detect_icmp() -> bool | None:
        try:
            from icmplib import async_ping  # noqa: PLC0415
        except ImportError:
            return None
        for privileged in (True, False):
            try:
                await async_ping("127.0.0.1", count=1, timeout=1, privileged=privileged)
            except Exception:  # noqa: BLE001 - SocketPermissionError & co.
                continue
            return privileged
        return None

    async def async_probe(self, ip: str, timeout: float = 0.8) -> tuple[bool, bool]:
        """Return (online, windows) for an address."""
        windows_tasks = [asyncio.create_task(_tcp_alive(ip, p, timeout)) for p in WINDOWS_PORTS]
        other_tasks = [asyncio.create_task(_tcp_alive(ip, p, timeout)) for p in OTHER_PORTS]
        ping_ok = await self._ping(ip, timeout)
        windows = any(await asyncio.gather(*windows_tasks))
        other = any(await asyncio.gather(*other_tasks))
        return ping_ok or windows or other, windows

    async def _ping(self, ip: str, timeout: float) -> bool:
        if self._icmp_privileged is None:
            return False
        from icmplib import async_ping  # noqa: PLC0415

        try:
            host = await async_ping(ip, count=1, timeout=timeout, privileged=self._icmp_privileged)
        except Exception:  # noqa: BLE001
            return False
        return host.is_alive


async def _tcp_alive(ip: str, port: int, timeout: float) -> bool:
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout)
    except ConnectionRefusedError:
        # An explicit refusal: the machine is there, that port is just closed.
        return True
    except (TimeoutError, OSError):
        return False
    writer.close()
    with contextlib.suppress(Exception):
        await writer.wait_closed()
    return True


def read_arp_table() -> dict[str, str]:
    """IP -> MAC from the kernel neighbour table (Linux). Blocking: run in executor."""
    table: dict[str, str] = {}
    try:
        with open("/proc/net/arp", encoding="ascii") as arp:
            next(arp, None)
            for line in arp:
                fields = line.split()
                # IP, HW type, Flags, HW address, Mask, Device. Flag 0x2 = complete entry.
                if len(fields) >= 4 and int(fields[2], 16) & 0x2:
                    mac = normalize_mac(fields[3])
                    if mac:
                        table[fields[0]] = mac
    except (OSError, ValueError):
        pass
    return table


async def async_reverse_dns(ip: str, timeout: float = 1.5) -> str | None:
    loop = asyncio.get_running_loop()
    try:
        host, _ = await asyncio.wait_for(loop.getnameinfo((ip, 0), socket.NI_NAMEREQD), timeout)
    except (TimeoutError, OSError, socket.gaierror):
        return None
    name = host.split(".")[0]
    return name if name and name != ip else None


# NetBIOS "node status" request for "*": Windows PCs answer with their name and MAC,
# even across a router when the firewall allows UDP 137.
_NBSTAT_REQUEST = bytes(
    [0x13, 0x37, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0x20, ord("C"), ord("K")]
    + [ord("A")] * 30
    + [0, 0, 0x21, 0, 1]
)


class _NetbiosProtocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.answer: asyncio.Future[bytes] = asyncio.get_running_loop().create_future()

    def datagram_received(self, data: bytes, addr) -> None:
        if not self.answer.done():
            self.answer.set_result(data)

    def error_received(self, exc: Exception) -> None:
        if not self.answer.done():
            self.answer.set_exception(exc)


async def async_netbios(ip: str, timeout: float = 0.7) -> tuple[str | None, str | None]:
    """Return (name, mac) from a NetBIOS node status query, or (None, None)."""
    loop = asyncio.get_running_loop()
    transport = None
    try:
        transport, protocol = await loop.create_datagram_endpoint(_NetbiosProtocol, remote_addr=(ip, 137))
        transport.sendto(_NBSTAT_REQUEST)
        data = await asyncio.wait_for(protocol.answer, timeout)
    except (TimeoutError, OSError):
        return None, None
    finally:
        if transport is not None:
            transport.close()
    return parse_netbios(data)


def parse_netbios(r: bytes) -> tuple[str | None, str | None]:
    try:
        if len(r) < 57:
            return None, None
        pos = 12
        pos += 2 if (r[pos] & 0xC0) == 0xC0 else 34  # answer name: pointer or full encoded name
        pos += 10  # type, class, TTL, data length
        count = r[pos]
        pos += 1
        name = None
        for i in range(count):
            p = pos + i * 18
            if p + 18 > len(r):
                return None, None
            suffix = r[p + 15]
            group = (r[p + 16] & 0x80) != 0
            if name is None and suffix == 0x00 and not group:
                name = r[p : p + 15].decode("ascii", "replace").strip()
        mac_pos = pos + count * 18
        mac = normalize_mac(r[mac_pos : mac_pos + 6].hex()) if mac_pos + 6 <= len(r) else None
        return (name or None), mac
    except IndexError:
        return None, None


def build_magic_packet(mac: str) -> bytes:
    raw = bytes.fromhex(mac.replace(":", ""))
    return b"\xff" * 6 + raw * 16


def wol_destinations(
    ip: str | None, subnet: ipaddress.IPv4Network | None, override: str | None
) -> list[str]:
    """Broadcast addresses to send the magic packet to for one device."""
    targets: list[str] = []
    if override:
        targets.append(override)
    if subnet is not None and subnet.prefixlen < 31:
        targets.append(str(subnet.broadcast_address))
    elif ip:
        # Unknown subnet: assume a /24 around the last known address.
        with contextlib.suppress(ValueError):
            targets.append(str(ipaddress.ip_network(f"{ip}/24", strict=False).broadcast_address))
    # The limited broadcast leaves from the default interface and covers the HA LAN.
    targets.append("255.255.255.255")
    return list(dict.fromkeys(targets))


def send_magic_packet(mac: str, destinations: list[str], repeat: int = 2) -> None:
    """Blocking: run in executor."""
    packet = build_magic_packet(mac)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        for _ in range(repeat):
            for destination in destinations:
                for port in WOL_PORTS:
                    try:
                        sock.sendto(packet, (destination, port))
                    except OSError as err:
                        # Destination not reachable from here (e.g. no route): go on with the others.
                        if err.errno not in (errno.ENETUNREACH, errno.EHOSTUNREACH, errno.EACCES):
                            _LOGGER.debug("WOL to %s:%s failed: %s", destination, port, err)
