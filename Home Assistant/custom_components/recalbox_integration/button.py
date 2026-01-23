# button.py
from homeassistant.components.button import ButtonEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    async_add_entities([
        RecalboxAPIButton(api, "Shutdown", "/api/system/shutdown", "mdi:power", 80),
        RecalboxAPIButton(api, "Reboot", "/api/system/reboot", "mdi:restart", 80),
        RecalboxScreenshotButton(api, entry.entry_id)
    ])

class RecalboxAPIButton(ButtonEntity):
    def __init__(self, api, name, path, icon, port=80):
        self._api = api
        self._path = path
        self._port = port
        self._attr_name = f"Recalbox {name}"
        self._attr_icon = icon

    async def async_press(self):
        # On envoie l'ordre API
        await self._api.post_api(self._path, self._port)
        # On peut même forcer le binaire à OFF ici pour le feedback immédiat !


class RecalboxScreenshotButton(ButtonEntity):
    def __init__(self, api, entry_id):
        self._api = api
        self._attr_name = "Recalbox Screenshot"
        self._attr_unique_id = f"{entry_id}_screenshot"
        self._attr_icon = "mdi:camera"

    async def async_press(self):
        print("Screen shot UDP, puis API si échec")
        # 1. Test UDP
        success = await self._api.send_udp_command(55355, "SCREENSHOT")
        # 2. Fallback API
        if not success:
            await self._api.post_api("/api/media/takescreenshot", port=81)


