"""Constants for the LAN Power Manager integration."""

DOMAIN = "lan_power_manager"

STORAGE_VERSION = 1
STORAGE_KEY = "lan_power_manager.devices"

PANEL_URL_PATH = "lan-power-manager"
PANEL_TITLE = "LAN Power"
PANEL_ICON = "mdi:lan"

# Config entry keys (data + options)
CONF_SUBNETS = "subnets"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_WIN_DOMAIN = "win_domain"
CONF_SCAN_INTERVAL = "scan_interval_minutes"
CONF_POLL_INTERVAL = "poll_interval_seconds"
CONF_SHUTDOWN_DELAY = "shutdown_delay"
CONF_SHUTDOWN_MESSAGE = "shutdown_message"
CONF_USER_POLICY = "user_policy"

DEFAULT_SCAN_INTERVAL = 60
DEFAULT_POLL_INTERVAL = 30
DEFAULT_SHUTDOWN_DELAY = 60

# Biggest subnet accepted for a scan (a /20): bigger ones take minutes and flood the LAN.
MAX_SCAN_HOSTS = 4094

# What to do when someone is logged on to a Windows PC that has to be switched off.
POLICY_FORCE = "force"  # warn, wait the delay, then shut down closing open programs
POLICY_SKIP = "skip"  # leave the PC on

SHUTDOWN_WINDOWS = "windows"
SHUTDOWN_SSH = "ssh"
SHUTDOWN_NONE = "none"
SHUTDOWN_METHODS = (SHUTDOWN_WINDOWS, SHUTDOWN_SSH, SHUTDOWN_NONE)

DEFAULT_SSH_PORT = 22
DEFAULT_SSH_COMMAND = "sudo -n shutdown -h now"
SSH_OS_WINDOWS = "windows"
SSH_OS_LINUX = "linux"
SSH_KEY_STORAGE_KEY = "lan_power_manager.ssh_key"
SSH_KEY_COMMENT = "home-assistant-lan-power-manager"

# How long a switch keeps showing the requested state while the PC boots / shuts down.
WAKE_TIMEOUT = 180
SHUTDOWN_TIMEOUT = 240
PENDING_POLL_SECONDS = 5

SIGNAL_DEVICES_UPDATED = f"{DOMAIN}_devices_updated"
SIGNAL_DEVICE_MAPPED = f"{DOMAIN}_device_mapped"
SIGNAL_DEVICE_UNMAPPED = f"{DOMAIN}_device_unmapped"

EVENT_NEW_DEVICE = f"{DOMAIN}_new_device"
EVENT_ACTION_RESULT = f"{DOMAIN}_action_result"
