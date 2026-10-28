"""Messages produced by the backend (errors, action outcomes), in English and Italian.

The panel and the config flow have their own translations; these are the texts built
at runtime (last_action, events, errors of the switch actions), picked by the
language Home Assistant is configured with.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant

MESSAGES: dict[str, dict[str, str]] = {
    "not_configured": {
        "en": "LAN Power Manager is not set up.",
        "it": "LAN Power Manager non è configurata.",
    },
    "default_shutdown_message": {
        "en": "This computer will be shut down by Home Assistant. Save your work.",
        "it": "Il computer verrà spento da Home Assistant. Salva il lavoro.",
    },
    "device_not_found": {
        "en": "Device {device_id} not found.",
        "it": "Dispositivo {device_id} non trovato.",
    },
    "mac_in_use": {
        "en": "MAC {mac} is already used by {other}.",
        "it": "Il MAC {mac} è già usato da {other}.",
    },
    "wol_disabled": {
        "en": "{name}: Wake-on-LAN is not enabled.",
        "it": "{name}: Wake-on-LAN non abilitato.",
    },
    "no_mac": {
        "en": "{name}: MAC address unknown, enter it in the panel.",
        "it": "{name}: MAC non noto, inseriscilo nel pannello.",
    },
    "no_ip": {
        "en": "{name}: IP address unknown.",
        "it": "{name}: indirizzo IP non noto.",
    },
    "no_shutdown_method": {
        "en": "{name}: no shutdown method configured.",
        "it": "{name}: nessun metodo di spegnimento configurato.",
    },
    "is_ha_host": {
        "en": "{name} is the computer Home Assistant runs on: not shutting it down.",
        "it": "{name} è il computer su cui gira Home Assistant: non lo spengo.",
    },
    "already_on": {"en": "Already on.", "it": "Già acceso."},
    "already_off": {"en": "Already off.", "it": "Già spento."},
    "turned_on": {"en": "Turned on.", "it": "Acceso."},
    "turned_off": {"en": "Turned off.", "it": "Spento."},
    "wol_sent": {
        "en": "Wake-on-LAN packet sent (MAC {mac}, to {destinations}, ports 9 and 7).",
        "it": "Pacchetto Wake-on-LAN inviato (MAC {mac}, a {destinations}, porte 9 e 7).",
    },
    "wake_failed": {
        "en": "No answer after the Wake-on-LAN packet: check WOL in the BIOS / network card settings and, "
        "if the computer is on another subnet, that the router forwards the broadcasts.",
        "it": "Non risponde dopo l'invio del pacchetto Wake-on-LAN: controlla il WOL nel BIOS/scheda di rete "
        "e, se il PC è in un'altra rete, l'inoltro dei broadcast sul router.",
    },
    "off_failed": {
        "en": "The computer still answers after the {action} command.",
        "it": "Il PC risponde ancora dopo il comando di {action}.",
    },
    # Names of the off actions, used inside other messages.
    "action_shutdown": {"en": "shutdown", "it": "spegnimento"},
    "action_hibernate": {"en": "hibernation", "it": "ibernazione"},
    "action_suspend": {"en": "suspend", "it": "sospensione"},
    "action_not_supported": {
        "en": "{name}: {action} is not available on macOS.",
        "it": "{name}: {action} non disponibile su macOS.",
    },
    "ssh_restricted_other": {
        "en": "{name}: the key installed on the computer only allows the \"{default}\" action, \"{action}\" "
        "is not possible. Turn off \"this action only\" (or change the off action) and install the key again.",
        "it": "{name}: la chiave installata sul PC permette solo l'azione \"{default}\", \"{action}\" non è "
        "possibile. Disattiva \"solo questa azione\" (o cambia l'azione allo spegnimento) e reinstalla la chiave.",
    },
    "missing_windows_credentials": {
        "en": "Windows credentials missing: set them in the options or on the device.",
        "it": "Credenziali Windows mancanti: impostale nelle opzioni o sul dispositivo.",
    },
    "missing_ssh_user": {
        "en": "SSH user missing: set it in the options or on the device.",
        "it": "Utente SSH mancante: impostalo nelle opzioni o sul dispositivo.",
    },
    # Windows / WMI
    "wmi_user_logged_on": {
        "en": "User logged on ({user}): not shutting down.",
        "it": "Utente collegato ({user}): non spengo.",
    },
    "wmi_refused": {
        "en": "Windows refused the shutdown command (code {code}).",
        "it": "Windows ha rifiutato il comando di spegnimento (codice {code}).",
    },
    "wmi_access_denied": {
        "en": "Access denied on {ip}: check username/password and that the account is an administrator of the "
        "computer (local accounts need LocalAccountTokenFilterPolicy=1).",
        "it": "Accesso negato su {ip}: controlla utente/password e che sia amministratore del PC "
        "(per gli account locali serve LocalAccountTokenFilterPolicy=1).",
    },
    "wmi_unreachable": {
        "en": "{ip} not reachable over RPC: computer off, or a firewall blocking WMI/RPC (port 135 and dynamic ports).",
        "it": "{ip} non raggiungibile via RPC: PC spento o firewall che blocca WMI/RPC (porta 135 e porte dinamiche).",
    },
    "wmi_error": {"en": "WMI error on {ip}: {error}", "it": "Errore WMI su {ip}: {error}"},
    "wmi_sent": {
        "en": "Requested over WMI: {action}{when}{user}.",
        "it": "Richiesto via WMI: {action}{when}{user}.",
    },
    "in_seconds": {"en": " in {delay} s", "it": " tra {delay} s"},
    "user_logged_on": {"en": ", user logged on: {user}", "it": ", utente collegato: {user}"},
    # SSH
    "ssh_no_host_key": {
        "en": "SSH to {ip}: the computer presented no identity key.",
        "it": "SSH su {ip}: il PC non ha presentato una chiave di identità.",
    },
    "ssh_identity_changed": {
        "en": "The identity of computer {ip} has changed: not connecting. If you reinstalled the system or "
        'replaced the computer, use "Forget identity" in the panel; otherwise someone is impersonating it.',
        "it": "L'identità del PC {ip} è cambiata: non mi collego. Se hai reinstallato il sistema o sostituito "
        'il PC, usa "Dimentica identità" nel pannello; altrimenti qualcuno si sta spacciando per il PC.',
    },
    "ssh_denied": {
        "en": "SSH to {ip}: access denied for user {user}. The Home Assistant key is not installed on the "
        "computer (or the user is wrong).",
        "it": "SSH su {ip}: accesso negato per l'utente {user}. La chiave di Home Assistant non è installata "
        "sul PC (o l'utente è sbagliato).",
    },
    "ssh_no_answer": {
        "en": "SSH to {ip}: no answer on port {port} (SSH server off or firewall).",
        "it": "SSH su {ip}: nessuna risposta sulla porta {port} (server SSH spento o firewall).",
    },
    "ssh_error": {"en": "SSH to {ip} failed: {error}", "it": "SSH su {ip} non riuscito: {error}"},
    "ssh_exit_code": {
        "en": "The SSH command ended with code {code}: {output}",
        "it": "Il comando SSH è terminato con codice {code}: {output}",
    },
    "ssh_login_ok": {
        "en": "SSH login with the Home Assistant key succeeded.",
        "it": "Accesso SSH riuscito con la chiave di Home Assistant.",
    },
    "ssh_login_ok_pinned": {
        "en": "SSH login with the Home Assistant key succeeded. Computer identity stored ({fingerprint}).",
        "it": "Accesso SSH riuscito con la chiave di Home Assistant. Identità del PC memorizzata ({fingerprint}).",
    },
    "ssh_sent": {
        "en": "Sent over SSH: {action}.",
        "it": "Inviato via SSH: {action}.",
    },
    "ssh_sent_closed": {
        "en": "Sent over SSH: {action} (connection closed by the computer).",
        "it": "Inviato via SSH: {action} (connessione chiusa dal PC).",
    },
}


@dataclass(frozen=True, slots=True)
class Message:
    """A message key with its placeholders, turned into text in the user's language later."""

    key: str
    placeholders: dict[str, Any] = field(default_factory=dict)

    def text(self, language: str) -> str:
        return translate(language, self.key, **self.placeholders)


def translate(language: str, key: str, **placeholders: Any) -> str:
    texts = MESSAGES[key]
    template = texts["it"] if (language or "").lower().startswith("it") else texts["en"]
    # A placeholder can itself be a Message (e.g. the name of an action).
    values = {k: v.text(language) if isinstance(v, Message) else v for k, v in placeholders.items()}
    return template.format(**values)


def ha_language(hass: HomeAssistant) -> str:
    return hass.config.language or "en"


class LocalizedError(Exception):
    """An error whose text is chosen when it reaches the user."""

    def __init__(self, key: str, **placeholders: Any) -> None:
        self.message = Message(key, placeholders)
        super().__init__(self.message.text("en"))
