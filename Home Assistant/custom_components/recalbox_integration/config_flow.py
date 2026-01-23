import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class RecalboxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le formulaire d'installation."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Etape lancée quand l'utilisateur ajoute l'intégration."""
        errors = {}
        if user_input is not None:
            # Ici tu pourrais ajouter un test de connexion à l'IP
            return self.async_create_entry(title=f"Recalbox ({user_input['host']})", data=user_input)

        # Définition du formulaire
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,  # On demande l'IP ou le hostname
            }),
            errors=errors,
        )