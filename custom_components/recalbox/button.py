# button.py
from homeassistant.components.button import ButtonEntity
from .const import DOMAIN
import asyncio

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        RecalboxProxyButton(entry, "Shutdown", "mdi:power"),
        RecalboxProxyButton(entry, "Reboot", "mdi:restart"),
        RecalboxProxyButton(entry, "Screenshot", "mdi:camera")
    ])

class RecalboxProxyButton(ButtonEntity):
    def __init__(self, entry, name, icon):
        self._entry = entry
        self._attr_name = f"Recalbox {name}"
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{name}"
        self._name = name

    @property
    def device_info(self):
        """Lien vers l'appareil parent."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
        }

    async def async_press(self):
        entity = self.hass.data[DOMAIN]["instances"][self._entry.entry_id].get("sensor_entity")
        if not entity:
            return

        if "Shutdown" in self._attr_name:
            await entity.request_shutdown()
        elif "Reboot" in self._attr_name:
            await entity.request_reboot()
        elif "Screenshot" in self._attr_name:
            await entity.request_screenshot()





