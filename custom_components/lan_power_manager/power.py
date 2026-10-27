"""Remote shutdown of the mapped computers.

Windows: WMI over DCOM/RPC (impacket, pure Python, so it works from Home Assistant
OS too): needs the RPC ports open on the PC firewall and an administrator account.
SSH (Windows, Linux, macOS): a command run with Home Assistant's own key (asyncssh).
Errors and outcomes are Message keys, turned into text in the user's language later.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging

from .messages import LocalizedError, Message
from .ssh_setup import windows_shutdown_command

_LOGGER = logging.getLogger(__name__)


class ShutdownError(LocalizedError):
    """The shutdown could not be delivered; the message is shown to the user."""


class UserLoggedOnError(ShutdownError):
    """Someone is logged on and the policy says to leave the PC on."""


@dataclass(slots=True)
class WindowsCredentials:
    username: str
    password: str
    domain: str = ""


def windows_shutdown(
    ip: str,
    credentials: WindowsCredentials,
    delay: int,
    message: str,
    skip_if_user: bool,
) -> Message:
    """Blocking (run in executor). Returns what happened."""
    # Imported here: impacket is big and only needed when a PC is actually switched off.
    from impacket.dcerpc.v5.dcom import wmi  # noqa: PLC0415
    from impacket.dcerpc.v5.dcomrt import DCOMConnection  # noqa: PLC0415
    from impacket.dcerpc.v5.dtypes import NULL  # noqa: PLC0415

    username = credentials.username
    domain = credentials.domain
    if not domain and "\\" in username:
        domain, username = username.split("\\", 1)

    dcom = None
    try:
        dcom = DCOMConnection(
            ip, username, credentials.password, domain, "", "", None, oxidResolver=True, doKerberos=False
        )
        interface = dcom.CoCreateInstanceEx(wmi.CLSID_WbemLevel1Login, wmi.IID_IWbemLevel1Login)
        login = wmi.IWbemLevel1Login(interface)
        services = login.NTLMLogin("//./root/cimv2", NULL, NULL)
        login.RemRelease()

        user = _console_user(services)
        if user and skip_if_user:
            raise UserLoggedOnError("wmi_user_logged_on", user=user)

        command = windows_shutdown_command(delay, message)
        process, _ = services.GetObject("Win32_Process")
        result = process.Create(command, "C:\\", None)
        code = _return_value(result)
        services.RemRelease()
        if code not in (0, None):
            raise ShutdownError("wmi_refused", code=code)
    except ShutdownError:
        raise
    except Exception as err:  # noqa: BLE001 - impacket raises many unrelated types
        raise _wmi_error(err, ip) from err
    finally:
        if dcom is not None:
            try:
                dcom.disconnect()
            except Exception:  # noqa: BLE001
                pass

    if user:
        return Message("wmi_sent_user", {"delay": delay, "user": user})
    return Message("wmi_sent", {"delay": delay})


def _console_user(services) -> str | None:
    """User on the PC console (Win32_ComputerSystem.UserName); RDP sessions are not listed."""
    try:
        query = services.ExecQuery("SELECT UserName FROM Win32_ComputerSystem")
        try:
            item = query.Next(0xFFFFFFFF, 1)[0]
            value = item.getProperties().get("UserName", {}).get("value")
        finally:
            query.RemRelease()
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Logged on user not read: %s", err)
        return None
    return value or None


def _return_value(result) -> int | None:
    try:
        return int(result.getProperties()["ReturnValue"]["value"])
    except Exception:  # noqa: BLE001
        return getattr(result, "ReturnValue", None)


def _wmi_error(err: Exception, ip: str) -> ShutdownError:
    text = str(err)
    lowered = text.lower()
    if "access_denied" in lowered or "rpc_s_access_denied" in lowered or "logon_failure" in lowered:
        return ShutdownError("wmi_access_denied", ip=ip)
    if isinstance(err, (TimeoutError, ConnectionRefusedError, OSError)) or "timed out" in lowered:
        return ShutdownError("wmi_unreachable", ip=ip)
    return ShutdownError("wmi_error", ip=ip, error=text.strip() or type(err).__name__)


@dataclass(slots=True)
class SshTarget:
    ip: str
    port: int
    username: str
    password: str | None
    client_key: str  # Home Assistant private key, OpenSSH format
    host_key: str | None  # pinned host key of the PC, None until the first connection


@dataclass(slots=True)
class SshResult:
    detail: Message
    learned_host_key: str | None = None  # set when the PC was seen for the first time
    learned_fingerprint: str | None = None


# Pin the strongest key the PC offers (asyncssh would otherwise pick RSA first).
_PREFERRED_HOST_KEY_ALGS = [
    "ssh-ed25519",
    "ecdsa-sha2-nistp256",
    "ecdsa-sha2-nistp384",
    "ecdsa-sha2-nistp521",
    "rsa-sha2-512",
    "rsa-sha2-256",
    "ssh-rsa",
]


def generate_client_key(comment: str) -> str:
    """Blocking (key generation): run in executor. Returns the private key, OpenSSH format."""
    import asyncssh  # noqa: PLC0415

    return asyncssh.generate_private_key("ssh-ed25519", comment=comment).export_private_key().decode()


def public_key_of(private_key: str) -> tuple[str, str]:
    """(OpenSSH public key line, SHA256 fingerprint)."""
    import asyncssh  # noqa: PLC0415

    key = asyncssh.import_private_key(private_key)
    return key.export_public_key().decode().strip(), key.get_fingerprint()


async def _async_ssh_connect(target: SshTarget):
    """Connect and authenticate, checking the PC identity BEFORE sending any credential.

    Returns (connection, learned host key or None, learned fingerprint or None).
    """
    import asyncssh  # noqa: PLC0415

    learned = learned_fp = None
    if target.host_key:
        trusted = asyncssh.import_public_key(target.host_key)
    else:
        # First contact: remember the key the PC presents (trust on first use).
        trusted = await asyncssh.get_server_host_key(
            target.ip, target.port, server_host_key_algs=_PREFERRED_HOST_KEY_ALGS, config=None
        )
        if trusted is None:
            raise ShutdownError("ssh_no_host_key", ip=target.ip)
        learned = trusted.export_public_key().decode().strip()
        learned_fp = trusted.get_fingerprint()

    conn = await asyncssh.connect(
        target.ip,
        port=target.port,
        username=target.username,
        password=target.password or None,
        client_keys=[asyncssh.import_private_key(target.client_key)],
        known_hosts=([trusted], [], []),
        agent_path=None,
        config=None,
        login_timeout=15,
    )
    return conn, learned, learned_fp


def _ssh_error(err: Exception, target: SshTarget) -> ShutdownError:
    import asyncssh  # noqa: PLC0415

    # KeyExchangeFailed: the PC no longer has a key of the pinned type at all.
    if isinstance(err, (asyncssh.HostKeyNotVerifiable, asyncssh.KeyExchangeFailed)) and target.host_key:
        return ShutdownError("ssh_identity_changed", ip=target.ip)
    if isinstance(err, asyncssh.PermissionDenied):
        return ShutdownError("ssh_denied", ip=target.ip, user=target.username)
    if isinstance(err, (TimeoutError, ConnectionRefusedError)):
        return ShutdownError("ssh_no_answer", ip=target.ip, port=target.port)
    return ShutdownError("ssh_error", ip=target.ip, error=str(err))


async def async_ssh_check(target: SshTarget) -> SshResult:
    """Log in and out without opening a session: safe even with a shutdown-only key."""
    import asyncssh  # noqa: PLC0415

    try:
        async with asyncio.timeout(40):
            conn, learned, learned_fp = await _async_ssh_connect(target)
            conn.close()
            await conn.wait_closed()
    except ShutdownError:
        raise
    except (OSError, asyncssh.Error, TimeoutError) as err:
        raise _ssh_error(err, target) from err
    if learned:
        return SshResult(Message("ssh_login_ok_pinned", {"fingerprint": learned_fp}), learned, learned_fp)
    return SshResult(Message("ssh_login_ok"), learned, learned_fp)


async def async_ssh_shutdown(target: SshTarget, command: str) -> SshResult:
    import asyncssh  # noqa: PLC0415

    try:
        async with asyncio.timeout(60):
            conn, learned, learned_fp = await _async_ssh_connect(target)
            async with conn:
                try:
                    result = await conn.run(command, check=False, timeout=20)
                except (TimeoutError, asyncssh.ConnectionLost, asyncssh.DisconnectError):
                    # The host often drops the connection while it is shutting down.
                    return SshResult(Message("ssh_sent_closed"), learned, learned_fp)
    except ShutdownError:
        raise
    except (OSError, asyncssh.Error, TimeoutError) as err:
        raise _ssh_error(err, target) from err

    if result.exit_status not in (0, None):
        output = str(result.stderr or result.stdout or "").strip()
        raise ShutdownError("ssh_exit_code", code=result.exit_status, output=output[:300])
    return SshResult(Message("ssh_sent"), learned, learned_fp)
