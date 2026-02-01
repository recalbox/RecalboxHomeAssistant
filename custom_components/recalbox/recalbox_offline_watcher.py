import logging
import socket
import asyncio
import async_timeout
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed, CoordinatorEntity
from collections import deque
from .api import RecalboxAPI

_LOGGER = logging.getLogger(__name__)

############################################
# Coordinateur                             #
# Pour vérifier toutes les 60 sec          #
# Si la Recalbox est encore ON par un ping #
############################################

frequency = timedelta(seconds=30)
maxHistoryLength = 4

async def prepare_ping_coordinator(hass, api:RecalboxAPI) -> DataUpdateCoordinator:
    _LOGGER.info(f"Prepare Recalbox watcher (coordinator). It will Ping the Recalbox {api.host} every {frequency}. When Pings reaches {maxHistoryLength} fails, it will automatically consider this Recalbox offline")
    # On garde un historique des 3 derniers résultats de Ping.
    # Si on a un seul ping qui échoue, ça évite de mettre la recalbox offline pour rien.
    # Avec un ping toutes les 30sec, on la passe en offline après 2 minutes comme ça.
    history = deque([], maxlen=maxHistoryLength)
    # 1. On définit le coordinateur pour le "Ping"
    async def async_update_data():
        """Vérifie si la Recalbox répond aux ping."""
        success = False
        resolved_ip = None
        try:
            async with async_timeout.timeout(5):
                success = await api.ping()
            # Resolve IP address from hostname here !
            # SEULEMENT si le ping est OK
            if success:
                try:
                  async with async_timeout.timeout(5):
                    # On demande l'IP correspondant au nom d'hôte pour la comparaison MQTT
                    resolved_ip = await hass.async_add_executor_job(
                        socket.gethostbyname, api.host
                    )
                    _LOGGER.debug(f"Recalbox {api.host} -> l'adresse IP {resolved_ip}")
                except Exception as dnsErr:
                    _LOGGER.debug(f"Failed to get DNS from Recalbox {api.host} : {dnsErr}")

        except Exception as err:
            # Si échec de connexion, on considère qu'elle est OFF
            _LOGGER.warning(f"Erreur au ping de la Recalbox {api.host}: {err}")
            success = False
        hasAnySuccessBefore = any(history)

        # On gère un historique pour "lisser" la présence
        history.append(success)
        _LOGGER.debug(f"Historique des pings sur la Recalbox {api.host} : {list(history)}")
        if any(history) :
            # The recalbox has Pings OK in the history
            _LOGGER.debug(f"The Recalbox {api.host} answers to ping, consider as probably online on IP {resolved_ip or 'unresolved'}.")
        elif hasAnySuccessBefore :
            # La recalbox n'a plus de Ping OK mais elle en avait juste avant
            _LOGGER.info(f"The Recalbox {api.host} doesnt answer to Pings anymore... Considering it as offline from now.")
        else :
            # La recalbox ne répondait déjà plus aux pings, reste dans la continuité
            _LOGGER.debug(f"The Recalbox {api.host} still not answering to pings.")

        return {
            "is_ping_success": success,
            "is_alive_smoothed": any(history),
            "mdns_ip_address": resolved_ip if success else None
        }


    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Recalbox Availability",
        update_method=async_update_data,
        update_interval=frequency, # Fréquence du check (ici: 30s)
    )

    # On lance le premier rafraîchissement
    await coordinator.async_config_entry_first_refresh()
    return coordinator