import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN
from .api import RecalboxAPI


# Schéma par défaut réutilisable
DATA_SCHEMA_CREATION = vol.Schema({
    vol.Required("host", default="recalbox.local"): str,
    vol.Required("api_port_os", default=80): int,
    vol.Required("api_port_gamesmanager", default=81): int,
    vol.Required("udp_recalbox", default=1337): int,
    vol.Required("udp_retroarch", default=55355): int,
    vol.Required("api_port_kodi", default=8081): int,
    vol.Required("test_connection", default=True): bool,
})

class RecalboxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le formulaire d'installation."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Etape lancée quand l'utilisateur ajoute l'intégration."""
        errors = {}
        if user_input is not None:
            if (user_input["test_connection"]):
                # tester un ping sur cette IP/host??
                api_temp = RecalboxAPI(
                    host=user_input["host"],
                    api_port_os=user_input["api_port_os"] or 80,
                    api_port_gamesmanager=user_input["api_port_gamesmanager"] or 81,
                    udp_recalbox=user_input["udp_recalbox"] or 1337,
                    udp_retroarch=user_input["udp_retroarch"] or 55355,
                    api_port_kodi=user_input["api_port_kodi"] or 8081,
                )
                is_valid = await api_temp.ping() and await api_temp.testPorts()
            else:
                is_valid = True

            if is_valid:
                user_input.pop("test_connection", None)
                return self.async_create_entry(
                    title=f"Recalbox ({user_input['host']})",
                    data=user_input
                )
            else:
                # Si on n'arrive pas à ping la recalbox, erreur
                errors["base"] = "cannot_connect"


        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(DATA_SCHEMA_CREATION, user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return RecalboxOptionsFlowHandler()


class RecalboxOptionsFlowHandler(config_entries.OptionsFlow):

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # self.config_entry est accessible automatiquement grâce à l'héritage
        current_config = {**self.config_entry.data, **self.config_entry.options}

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("host", default=current_config.get("host", "recalbox.local")): str,
                vol.Required("api_port_os", default=current_config.get("api_port_os", 80)): int,
                vol.Required("api_port_gamesmanager", default=current_config.get("api_port_gamesmanager", 81)): int,
                vol.Required("udp_recalbox", default=current_config.get("udp_recalbox", 1337)): int,
                vol.Required("udp_retroarch", default=current_config.get("udp_retroarch", 55355)): int,
                vol.Required("api_port_kodi", default=current_config.get("api_port_kodi", 8081)): int,
            }),
        )