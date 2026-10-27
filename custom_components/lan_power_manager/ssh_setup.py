"""Shutdown commands and the setup scripts shown in the panel for SSH devices.

Home Assistant has one key pair of its own: the public half goes into the
authorized keys of each PC. With "only shutdown" the key line carries a forced
command (OpenSSH `restrict,command="..."`), so that key can do nothing else on
the PC, whatever command the client asks for.
"""
from __future__ import annotations

from .const import DEFAULT_SSH_COMMAND, SSH_OS_WINDOWS

WINDOWS_KEYS_FILE = r"C:\ProgramData\ssh\administrators_authorized_keys"


def sanitize_message(message: str) -> str:
    # shutdown.exe /c takes at most 512 characters inside double quotes.
    return message.replace('"', "'").replace("\r", " ").replace("\n", " ").strip()[:500]


def windows_shutdown_command(delay: int, message: str | None) -> str:
    command = f"shutdown /s /f /t {max(0, int(delay))}"
    if message and delay > 0:
        command += f' /c "{sanitize_message(message)}"'
    return command


def shutdown_command(ssh_os: str, custom: str | None, delay: int, message: str | None) -> str:
    if custom:
        return custom
    if ssh_os == SSH_OS_WINDOWS:
        return windows_shutdown_command(delay, message)
    return DEFAULT_SSH_COMMAND


def authorized_keys_line(public_key: str, restricted: bool, command: str) -> str:
    """The line to add to the PC authorized keys."""
    if not restricted:
        return public_key
    # In authorized_keys options a double quote is escaped with a backslash.
    return f'restrict,command="{command.replace(chr(34), chr(92) + chr(34))}" {public_key}'


def _ps_literal(value: str) -> str:
    """A PowerShell single-quoted string: nothing inside is interpreted, quotes are doubled."""
    return "'" + value.replace("'", "''") + "'"


def _sh_literal(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def windows_setup_script(public_key: str, line: str) -> str:
    """PowerShell to paste in an administrator PowerShell on the PC.

    Installs and starts the OpenSSH server, opens port 22 and writes the key in the
    file that Windows uses for the administrators, with the only permissions it accepts.
    """
    key_body = public_key.split()[1]
    return "\n".join(
        [
            "# LAN Power Manager (Home Assistant) - run in PowerShell as administrator",
            "$ErrorActionPreference = 'Stop'",
            "$cap = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'",
            "if ($cap.State -ne 'Installed') { Add-WindowsCapability -Online -Name $cap.Name | Out-Null }",
            "Set-Service -Name sshd -StartupType Automatic",
            "Start-Service sshd",
            "if (-not (Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -ErrorAction SilentlyContinue)) {",
            "  New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'OpenSSH Server (sshd)' "
            "-Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 | Out-Null",
            "}",
            f"$file = {_ps_literal(WINDOWS_KEYS_FILE)}",
            f"$key = {_ps_literal(key_body)}",
            f"$line = {_ps_literal(line)}",
            "# Replace any previous line with the same key",
            "$lines = @(if (Test-Path $file) { Get-Content $file | Where-Object { $_ -and $_ -notlike \"*$key*\" } })",
            "[IO.File]::WriteAllLines($file, [string[]]($lines + $line))",
            "# Administrators and SYSTEM only, otherwise sshd ignores the file",
            "icacls $file /inheritance:r /grant '*S-1-5-32-544:F' /grant '*S-1-5-18:F' | Out-Null",
            "Write-Host 'Home Assistant key installed.' -ForegroundColor Green",
        ]
    )


def linux_setup_script(public_key: str, line: str) -> str:
    """Shell commands to run as the user Home Assistant will log in with."""
    key_body = public_key.split()[1]
    return "\n".join(
        [
            "# LAN Power Manager (Home Assistant) - run as the user Home Assistant logs in with",
            "mkdir -p ~/.ssh && chmod 700 ~/.ssh",
            "touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys",
            f"grep -v {_sh_literal(key_body)} ~/.ssh/authorized_keys > ~/.ssh/authorized_keys.tmp || true",
            f"echo {_sh_literal(line)} >> ~/.ssh/authorized_keys.tmp",
            "mv ~/.ssh/authorized_keys.tmp ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys",
            "# Let the user shut down without a password",
            'echo "$USER ALL=(root) NOPASSWD: /sbin/shutdown, /usr/sbin/shutdown" '
            "| sudo tee /etc/sudoers.d/home-assistant-shutdown > /dev/null",
            "sudo chmod 440 /etc/sudoers.d/home-assistant-shutdown",
        ]
    )


def setup_script(ssh_os: str, public_key: str, restricted: bool, command: str) -> str:
    line = authorized_keys_line(public_key, restricted, command)
    if ssh_os == SSH_OS_WINDOWS:
        return windows_setup_script(public_key, line)
    return linux_setup_script(public_key, line)
