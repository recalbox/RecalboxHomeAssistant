import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN


# Schéma par défaut réutilisable
DATA_SCHEMA = vol.Schema({
    vol.Required("host", default="recalbox.local"): str,
    vol.Required("api_port_os", default=80): int,
    vol.Required("api_port_webmanager", default=81): int,
    vol.Required("udp_recalbox", default=1337): int,
    vol.Required("udp_emulstation", default=55355): int,
})

class RecalboxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le formulaire d'installation."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Etape lancée quand l'utilisateur ajoute l'intégration."""
        errors = {}
        if user_input is not None:
            # Ici tu pourrais ajouter un test de connexion à l'IP
            return self.async_create_entry(title=f"Recalbox ({user_input['host']})", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
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
                vol.Required("api_port_webmanager", default=current_config.get("api_port_webmanager", 81)): int,
                vol.Required("udp_recalbox", default=current_config.get("udp_recalbox", 1337)): int,
                vol.Required("udp_emulstation", default=current_config.get("udp_emulstation", 55355)): int,
            }),
        )