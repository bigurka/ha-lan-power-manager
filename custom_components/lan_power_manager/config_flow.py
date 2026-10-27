"""Config flow for LAN Power Manager.

Single instance. The wizard asks only for the subnets to scan and the default
credentials used to switch computers off; which devices are mapped (and so get a
switch) is decided in the LAN Power Manager sidebar panel.
"""
from __future__ import annotations

import ipaddress
from typing import Any

import voluptuous as vol

from homeassistant.components import network
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

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
    DOMAIN,
    MAX_SCAN_HOSTS,
    POLICY_FORCE,
    POLICY_SKIP,
)
from .messages import ha_language, translate
from .network import parse_subnets

_PASSWORD = selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD))


async def _default_subnets(hass: HomeAssistant) -> str:
    """The IPv4 networks Home Assistant is attached to (enabled adapters)."""
    subnets: list[str] = []
    for adapter in await network.async_get_adapters(hass):
        if not adapter["enabled"]:
            continue
        for addr in adapter["ipv4"]:
            net = ipaddress.ip_network(f"{addr['address']}/{addr['network_prefix']}", strict=False)
            if not net.is_loopback and net.prefixlen <= 30:
                # Larger than a /20 would take too long: fall back to the /24 around HA.
                if net.num_addresses > MAX_SCAN_HOSTS + 2:
                    net = ipaddress.ip_network(f"{addr['address']}/24", strict=False)
                subnets.append(str(net))
    return ", ".join(dict.fromkeys(subnets))


def _validate_subnets(value: str) -> str | None:
    """Return an error key, or None if the subnets are fine."""
    try:
        subnets = parse_subnets(value)
    except ValueError:
        return "invalid_subnet"
    if not subnets:
        return "no_subnet"
    if any(n.num_addresses > MAX_SCAN_HOSTS + 2 for n in subnets):
        return "subnet_too_large"
    return None


def _main_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_SUBNETS, default=defaults.get(CONF_SUBNETS, "")): str,
            vol.Optional(
                CONF_USERNAME, description={"suggested_value": defaults.get(CONF_USERNAME)}
            ): str,
            vol.Optional(CONF_PASSWORD): _PASSWORD,
            vol.Optional(
                CONF_WIN_DOMAIN, description={"suggested_value": defaults.get(CONF_WIN_DOMAIN)}
            ): str,
        }
    )


class LanPowerConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}
        if user_input is not None:
            if error := _validate_subnets(user_input[CONF_SUBNETS]):
                errors[CONF_SUBNETS] = error
            else:
                return self.async_create_entry(title="LAN Power Manager", data=user_input)

        defaults = user_input or {CONF_SUBNETS: await _default_subnets(self.hass)}
        return self.async_show_form(
            step_id="user", data_schema=_main_schema(defaults), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return LanPowerOptionsFlow()


class LanPowerOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            if error := _validate_subnets(user_input[CONF_SUBNETS]):
                errors[CONF_SUBNETS] = error
            else:
                # A blank password field keeps the stored password.
                if not user_input.get(CONF_PASSWORD):
                    user_input[CONF_PASSWORD] = current.get(CONF_PASSWORD, "")
                return self.async_create_entry(data=user_input)

        defaults = user_input or current
        schema = _main_schema(defaults).extend(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL, default=int(defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=1440, step=5, unit_of_measurement="min",
                                                  mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_POLL_INTERVAL, default=int(defaults.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL))
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=10, max=600, step=5, unit_of_measurement="s",
                                                  mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_SHUTDOWN_DELAY, default=int(defaults.get(CONF_SHUTDOWN_DELAY, DEFAULT_SHUTDOWN_DELAY))
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=600, step=5, unit_of_measurement="s",
                                                  mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(
                    CONF_SHUTDOWN_MESSAGE,
                    default=defaults.get(CONF_SHUTDOWN_MESSAGE)
                    or translate(ha_language(self.hass), "default_shutdown_message"),
                ): str,
                vol.Required(
                    CONF_USER_POLICY, default=defaults.get(CONF_USER_POLICY, POLICY_FORCE)
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[POLICY_FORCE, POLICY_SKIP], translation_key=CONF_USER_POLICY
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
