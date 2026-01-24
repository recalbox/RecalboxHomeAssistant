# button.py
from homeassistant.components.button import ButtonEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    # Fonction pour forcer le statut à OFF dans HA
    async def force_off():
        # On cherche l'entité binary_sensor dans le registre d'états
        # Note: Adaptez le nom si votre entité ne suit pas ce pattern exact
        entity_id = f"binary_sensor.recalbox_{entry.data.get('host').replace('.', '_')}"
        state = hass.states.get(entity_id)
        if state:
            # On force l'état à 'off' manuellement
            hass.states.async_set(entity_id, "off", state.attributes)

    async_add_entities([
        RecalboxAPIButton(api, "Shutdown", "/api/system/shutdown", "mdi:power", entry, 80, callback=force_off),
        RecalboxAPIButton(api, "Reboot", "/api/system/reboot", "mdi:restart", entry, 80),
        RecalboxScreenshotButton(api, entry)
    ])

class RecalboxAPIButton(ButtonEntity):
    def __init__(self, api, name, path, icon, entry, port=80, callback=None):
        self._api = api
        self._path = path
        self._port = port
        self._config_entry = entry
        self._attr_name = f"Recalbox {name}"
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{name}"
        self._name = name
        self._callback = callback

    @property
    def device_info(self):
        """Lien vers l'appareil parent."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
        }

    async def async_press(self):
        # On envoie l'ordre API
        await self._api.post_api(self._path, self._port)
        # Si un callback est défini (pour Shutdown), on l'exécute
        if self._callback:
            await self._callback()


class RecalboxScreenshotButton(ButtonEntity):
    def __init__(self, api, entry):
        self._api = api
        self._attr_name = "Recalbox Screenshot"
        self._attr_unique_id = f"{entry.entry_id}_screenshot"
        self._attr_icon = "mdi:camera"
        self._config_entry = entry

    @property
    def device_info(self):
        """Lien vers l'appareil parent."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
        }

    async def async_press(self):
        self._api.screenshot()


