from homeassistant.components.mqtt import async_subscribe
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed, CoordinatorEntity
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN
import unicodedata
import re
import homeassistant.helpers.config_validation as cv
import json
import asyncio
import logging
import async_timeout
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)


############################################
# Coordinateur                             #
# Pour vérifier toutes les 60 sec          #
# Si la Recalbox est encore ON par un ping #
############################################

async def prepare_ping_coordinator(hass, api) -> DataUpdateCoordinator:
    # 1. On définit le coordinateur pour le "Ping"
    async def async_update_data():
        """Vérifie si la Recalbox répond toujours sur son API."""
        try:
            async with async_timeout.timeout(5):
                return await api.ping()
        except Exception as err:
            # Si échec de connexion, on considère qu'elle est OFF
            return False

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Recalbox Availability",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30), # Fréquence du check (ici: 30s)
    )

    # On lance le premier rafraîchissement
    await coordinator.async_config_entry_first_refresh()
    return coordinator




async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configuration des entités Recalbox à partir de la config entry."""
    api = hass.data[DOMAIN]["instances"][config_entry.entry_id]["api"]
    coordinator = await prepare_ping_coordinator(hass, api)
    # On crée l'entité en lui passant l'objet config_entry (qui contient l'IP)
    new_entity = RecalboxEntityMQTT(hass, config_entry, api, coordinator)
    hass.data[DOMAIN]["instances"][config_entry.entry_id]["sensor_entity"] = new_entity # pour la retrouver ailleurs plus facilement
    async_add_entities([new_entity])




class RecalboxEntityMQTT(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, hass, config_entry, api, coordinator):
        super().__init__(coordinator)
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

    @property
    def is_on(self) -> bool:
        """L'entité est ON si MQTT dit ON ET que le dernier ping a réussi."""
        if not self.coordinator.data:
            return False
        return self._attr_is_on

    # Dans binary_sensor.py
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": f"Recalbox ({self._ip})",
            "manufacturer": "Aurélien Tomassini for Recalbox",
            "model": "Recalbox OS Integration",
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


    #################################
    #             ACTIONS           #
    #################################

    # Dans binary_sensor.py, classe RecalboxEntityMQTT
    async def _force_status_off(self):
        _LOGGER.debug("Forcing Recalbox status OFF (sans attendre MQTT)")
        self._attr_is_on = False
        self.async_write_ha_state()


    # Exemple : Action appelée par un service ou un bouton
    async def request_turn_on(self, **kwargs) -> bool:
        """Appelé quand on clique sur ON dans l'interface."""
        return await self.send_udp_command("POWER_ON")


    async def request_shutdown(self) -> bool:
        _LOGGER.debug("Shut down Recalbox via API")
        if await self._api.post_api("/api/system/shutdown", port=80) :
            await asyncio.sleep(5)
            await self._force_status_off()
            return True
        else:
            return False


    async def request_reboot(self) -> bool :
        _LOGGER.debug("Reboot Recalbox via API")
        if await self._api.post_api("/api/system/reboot", port=80) :
            await asyncio.sleep(5)
            await self._force_status_off()
            return True
        else:
            return False


    async def request_screenshot(self) -> bool :
        _LOGGER.debug("Screenshot UDP, puis API si échec")
        # 1. Test UDP
        success = await self._api.send_udp_command(55355, "SCREENSHOT")
        # 2. Fallback API
        if not success:
            _LOGGER.warning("Screenshot UDP command not sent on port 55355. Please check your Recalbox is has this port running. Will now try a screenshot via API...")
            return await self._api.post_api("/api/media/takescreenshot", port=81)
        else:
            _LOGGER.debug("Screenshot UDP command sent successfully to Recalbox")
            return True


    async def request_quit_current_game(self) -> bool :
        _LOGGER.debug("Quit current game via UDP")
        return await self._api.send_udp_command(55355, "QUIT")


    async def request_pause_game(self) -> bool :
        _LOGGER.debug("(Un)Pause current game via UDP")
        return await self._api.send_udp_command(55355, "PAUSE_TOGGLE")


    async def ping_recalbox(self) -> bool :
        _LOGGER.debug("Ping recalbox")
        try:
            async with async_timeout.timeout(5):
                return await self._api.ping()
        except Exception as err:
            return False


    # Renvoie le texte pour Assist
    async def search_and_launch_game_by_name(self, console, game_query, lang=None) -> str :
        _LOGGER.debug(f"Try to launch game {game_query} on system {console}")
        translator = self.hass.data[DOMAIN]["translator"]
        # Récupérer la liste des roms via l'API (HTTP GET)
        try:
            roms = await self._api.get_roms(console)
            if not roms:
                return translator.translate(
                    "intent_response.no_game_on_system",
                    {"console": console},
                    lang = lang
                )
        except:
            return translator.translate("intent_response.list_roms_failed", lang=lang)


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
            _LOGGER.debug(f"Game found, with name {target['name']}, on system {console}. Try to launch via UDP command...")
            try:
                await self._api.send_udp_command(1337, f"START|{console}|{target['path']}")
                _LOGGER.debug(f"Game launched !")
                return translator.translate(
                    "intent_response.game_launched_success",
                    {"console": console, "game": target['name']},
                    lang=lang
                )
            except Exception as err:
                _LOGGER.error(f"Failed to launch game {target['name']} on {console} : {err}")
                return translator.translate(
                    "intent_response.game_launched_error",
                    {"console": console, "game": target['name']},
                    lang=lang
                )
        else:
            _LOGGER.info(f"No game matching {game_query} on {console} !")
            return translator.translate(
                "intent_response.game_not_found_on_console",
                {"console": console, "game":game_query},
                lang=lang
            )


    ##########################
    #       Ecoute MQTT      #
    ##########################

    # Callback, une fois ajouté à HASS
    # on souscrit aux files MQTT
    # pour mettre à jour la Recalbox selon
    # les messages reçus
    async def async_added_to_hass(self):
        """Appelé quand l'entité est ajoutée à HA."""
        await super().async_added_to_hass()

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

