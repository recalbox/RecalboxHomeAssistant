from homeassistant.components.mqtt import async_subscribe
from homeassistant.components.binary_sensor import BinarySensorEntity
from .const import DOMAIN
import unicodedata
import re
import homeassistant.helpers.config_validation as cv
import json
import asyncio

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configuration des entités Recalbox à partir de la config entry."""
    api = hass.data[DOMAIN]["instances"][config_entry.entry_id]["api"]
    # On crée l'entité en lui passant l'objet config_entry (qui contient l'IP)
    new_entity = RecalboxEntityMQTT(hass, config_entry, api)
    hass.data[DOMAIN]["instances"][config_entry.entry_id]["sensor_entity"] = new_entity # pour la retrouver ailleurs plus facilement
    async_add_entities([new_entity])

class RecalboxEntityMQTT(BinarySensorEntity):
    def __init__(self, hass, config_entry, api):
        self.hass = hass # On récupère l'IP stockée dans la config
        self._config_entry = config_entry
        self._ip = config_entry.data.get("host")
        self._api = api
        self._attr_unique_id = f"{config_entry.entry_id}_status"
        self._attr_name = f"Recalbox {self._ip}"
        self._attr_icon = "mdi:gamepad-variant-outline"
        self._attr_is_on = False
        self._attr_extra_state_attributes = {}
        # Attribut volatile (non persisté dans l'objet d'état standard)
        self.game = "-"
        self.console = "-"
        self.rom = "-"
        self.genre = "-"
        self.genreId = "-"
        self.imageUrl = "-"

    # Dans binary_sensor.py
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"Recalbox ({self._ip})",
            "manufacturer": "Aurelien Tomassini",
            "model": "Recalbox Integration",
            "configuration_url": f"http://{self._ip}",
            "sw_version": self._attr_extra_state_attributes.get("recalboxVersion", "-"),
            "hw_version": self._attr_extra_state_attributes.get("hardware", "-"),
        }

    @property
    def extra_state_attributes(self):
        """Retourne les attributs de l'état."""
        global_data = self.hass.data.get(DOMAIN, {}).get("global", {})
        return {
            **self._attr_extra_state_attributes, # Les persistants (version, hw)
            "game": self.game,
            "console": self.console,
            "genre": self.genre,
            "genreId": self.genreId,
            "rom": self.rom,
            "imageUrl": self.imageUrl,
            "needs_restart": global_data.get("needs_restart", False)
        }

    async def async_added_to_hass(self):
        """Appelé quand l'entité est ajoutée à HA."""

        async def message_received(msg):
            """Logique lors de la réception d'un message MQTT."""
            topic = msg.topic
            payload = msg.payload

            # 1. Gestion du Status (ON/OFF)
            if topic == "recalbox/notifications/status":
                print('Updating recalbox status')
                self._attr_is_on = (payload == "ON")

            # 2. Gestion des infos du Jeu (JSON)
            elif topic == "recalbox/notifications/game":
                print('Updating recalbox current game')
                try:
                    data = json.loads(payload)

                    # 1. Mise à jour des attributs internes
                    v_sw = data.get("recalboxVersion")
                    v_hw = data.get("hardware")

                    self._attr_extra_state_attributes.update({
                        "hardware": v_hw,
                        "recalboxVersion": v_sw
                    })

                    self.game = data.get("game", "-")
                    self.console = data.get("console", "-")
                    self.genre = data.get("genre", "-")
                    self.genreId = data.get("genreId", "-")
                    self.rom = data.get("rom", "-")
                    self.imageUrl = data.get("imageUrl", "-")


                    print('Updating device version/hardware')
                    # On signale à HA que les infos du device ont pu changer
                    from homeassistant.helpers import device_registry as dr
                    device_registry = dr.async_get(self.hass)
                    device = device_registry.async_get_device(
                        identifiers={(DOMAIN, self._config_entry.entry_id)}
                    )
                    if device:
                        device_registry.async_update_device(
                            device.id,
                            sw_version=v_sw,
                            hw_version=v_hw
                        )

                except json.JSONDecodeError:
                    pass

            # Notifier HA du changement
            self.async_write_ha_state()

        # Abonnement au topic
        await async_subscribe(self.hass, "recalbox/notifications/status", message_received)
        await async_subscribe(self.hass, "recalbox/notifications/game", message_received)
        print("Abonnement à recalbox/notifications/status et recalbox/notifications/game")



    # Dans binary_sensor.py, classe RecalboxEntityMQTT
    async def force_status_off(self):
        """Force l'état à OFF sans attendre MQTT."""
        self._attr_is_on = False
        self.async_write_ha_state()


    # Exemple : Action appelée par un service ou un bouton
    async def request_turn_on(self, **kwargs) -> bool:
        """Appelé quand on clique sur ON dans l'interface."""
        return await self.send_udp_command("POWER_ON")


    async def request_shutdown(self) -> bool:
        if await self._api.post_api("/api/system/shutdown", port=80) :
            await asyncio.sleep(5)
            await self.force_status_off()
            return True
        else:
            return False


    async def request_reboot(self) -> bool :
        if await self._api.post_api("/api/system/reboot", port=80) :
            await asyncio.sleep(5)
            await self.force_status_off()
            return True
        else:
            return False


    async def request_screenshot(self) -> bool :
        print("Screen shot UDP, puis API si échec")
        # 1. Test UDP
        success = await self._api.send_udp_command(55355, "SCREENSHOT")
        # 2. Fallback API
        if not success:
            return await self._api.post_api("/api/media/takescreenshot", port=81)
        else:
            return True


    # Renvoie le texte pour Assist
    async def search_and_launch_game_by_name(self, console, game_query) -> str :
        # Récupérer la liste des roms via l'API (HTTP GET)
        roms = await self._api.get_roms(console)
        if not roms:
            return f"Aucun jeu trouvé sur la console {console}."

        def normalize_str(s):
            if not s: return ""
            # Supprime les accents et met en minuscule
            s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8')
            return s.lower().strip()

        query_simplified = normalize_str(game_query)
        pattern = query_simplified.replace(" ", ".*")

        target = None
        for r in roms:
            # On simplifie le nom du fichier/jeu pour la comparaison
            name_simplified = normalize_str(r.get('name', ''))
            # Recherche RegEx (l'ordre est respecté grâce au .*)
            if re.search(pattern, name_simplified):
                target = r
                break

        if target:
            await self._api.send_udp_command(1337, f"START|{console}|{target['path']}")
            return f"Le jeu {target['name']} a bien été trouvé. Lancement sur {console} !"
        else:
            return f"Le jeu {game_query} n'a pas été trouvé sur {console}."