from homeassistant.components.mqtt import async_subscribe
from homeassistant.components.binary_sensor import BinarySensorEntity
import json
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configuration des entités Recalbox à partir de la config entry."""
    # On crée l'entité en lui passant l'objet config_entry (qui contient l'IP)
    new_entity = RecalboxEntityMQTT(hass, config_entry)
    async_add_entities([new_entity])

class RecalboxEntityMQTT(BinarySensorEntity):
    def __init__(self, hass, config_entry):
        self.hass = hass # On récupère l'IP stockée dans la config
        self._config_entry = config_entry
        self._ip = config_entry.data.get("host")
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
        return {
            **self._attr_extra_state_attributes, # Les persistants (version, hw)
            "game": self.game,
            "console": self.console,
            "genre": self.genre,
            "genreId": self.genreId,
            "rom": self.rom,
            "imageUrl": self.imageUrl
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


    # Exemple : Action appelée par un service ou un bouton
    async def async_turn_on(self, **kwargs):
        """Appelé quand on clique sur ON dans l'interface."""
        await self.send_udp_command("POWER_ON")