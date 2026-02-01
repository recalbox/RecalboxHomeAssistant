#!/bin/bash

# Script : https://wiki.recalbox.com/fr/advanced-usage/scripts-on-emulationstation-events
# A placer dans le dossier userscripts
# Par Aurélien Tomassini

SCRIPT_VERSION="home_assistant_notifier(permanent).sh:v1.4.0"

# Configuration
HOME_ASSISTANT_DOMAIN="homeassistant.local"
MQTT_USER="recalbox"
MQTT_PASS="recalpass"
TOPIC="recalbox/notifications"
# Chemin du fichier d'état Recalbox
STATE_FILE="/tmp/es_state.inf"
LOGS_FOLDER="/recalbox/share/system/logs/home_assistant_integration"



# MQTT localpour écouter les événements Recalbox
MQTT_LOCAL_HOST="127.0.0.1"
MQTT_LOCAL_PORT=1883
TOPIC_LOCAL="Recalbox/EmulationStation/Event"

# Variables d'état
RECALBOX_VERSION=$(cat /recalbox/recalbox.version 2>/dev/null || echo "Inconnue")
HARDWARE_MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo "Hardware inconnu")
# l'IP sera récupérée via mDNS une fois connecté au réseau
HA_IP=""





#------ Outils ------


prepare_logs_file() {
  # logs : 1 dossier par jour
  LOG_DIR="$LOGS_FOLDER/$(date '+%Y-%m-%d')"
  # On crée le dossier de logs du jour, s'il n'existe pas encore
  if [[ $ACTION == "start" ]]; then
    # Démarrage : on efface tous les anciens logs
    find "$LOGS_FOLDER/" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +
  elif [ ! -f "$HOME_ASSISTANT_IP_CACHE_FILE" ]; then
    # On a déjà démarré.
    # Si on n'a pas encore récupéré l'adresse IP de HomeAssistant <-> dans les premiers lancements,
    # Alors on va nettoyer les anciens logs (sauf le dossier du jour):

    # On supprime les dossiers de logs des autres jours, pour pas tout garder pour rien :
    # on cherche les dossiers (-type d) dans le répertoire parent,
    # on exclut le dossier parent lui-même (!) et celui du jour (! -path),
    # puis on supprime.
    find "$LOGS_FOLDER/" -mindepth 1 -maxdepth 1 -type d ! -path "$LOG_DIR" -exec rm -rf {} +
  fi
  mkdir -p "$LOG_DIR"
  # Et enfin on crée le fichier le logs de cette instance du script
  LOG_FILE="$LOG_DIR/home_assistant_notifier_$(date '+%Y-%m-%d_%H%M%S')_$ACTION.log"
  exec > "$LOG_FILE" 2>&1 # Redirige les sorties vers le fichier
}


# Ecriture dans les logs
log() {
  echo "[ $(date '+%Y-%m-%d %H:%M:%S') ] $1" >&2
}

# Fonction pour extraire une valeur par sa clé
get_val() {
  # Cherche la ligne commençant par la clé, extrait ce qui est après le premier =
  grep "^$1=" "$STATE_FILE" | cut -d'=' -f2- | tr -d '\r' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

# Nettoyage des variables pour le JSON
clean_json_val() {
  if [ -z "$1" ] || [ "$1" == "null" ]; then
    echo "null";
  else
    echo "\"$1\"";
  fi
}

# Tentative de récupération de l'IP Home Assistant (seulement si pas encore connue)
update_ha_ip() {
  # On récupère l'IP (la première trouvée)
  IP_LOCALE=$(ip -4 addr show scope global | awk '/inet / {print $2}' | cut -d/ -f1 | head -n 1)

  if [ -z "$HA_IP" ]; then
    # On vérifie si le réseau est là en tentant une résolution
    HA_IP=$(avahi-resolve -n "$HOME_ASSISTANT_DOMAIN" -4 | cut -f2)
    if [ -n "$HA_IP" ]; then
      log "Home Assistant accessible via $HA_IP"
    fi
  fi
}

clear_game() {
  GAME_NAME="null"
  ROM="null"
  GAME_IMAGE_PATH="null"
  GAME_GENRE="null"
  GAME_GENRE_ID="null"
}


send_mqtt() {
  local sub_topic="$1"
  local message="$2"
  local retain_flag=""

  # Si on n'a pas d'IP, on n'essaye même pas d'envoyer
  [ -z "$HA_IP" ] && return

  [ "$3" == "true" ] && retain_flag="-r"
  mosquitto_pub -h "$HA_IP" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$TOPIC/$sub_topic" -m "$message" $retain_flag
  log "Message MQTT envoyé à $HA_IP, sur $TOPIC/$sub_topic : $message"
}



#----- Script permanent -----
# Voir si le script tourne :      ps auxw | grep "assistant"
# Lancer le script à la main :    bash -x "/recalbox/share/userscripts/home_assistant_notifier(permanent).sh"
# générer un événement fake:      mosquitto_pub -h 127.0.0.1 -t "/Recalbox/EmulationStation/Event" -m "start"
# voir les logs de cet outil:     tail -f "/recalbox/share/saves/home_assistant_notifier.log"

prepare_logs_file

log "Démarrage du démon de notification Home Assistant par MQTT..."

while true; do

  # Débloquer avec
  # mosquitto_pub -h 127.0.0.1 -t "/Recalbox/EmulationStation/Event" -m "start"
  # pour déclencher un événement MQTT
  log "En attente d'un nouvel événement..."
  EVENT=$(mosquitto_sub -h "$MQTT_LOCAL_HOST" -p $MQTT_LOCAL_PORT -q 0 -t "$TOPIC_LOCAL" -C 1)

  case "$EVENT" in
    start|systembrowsing|endgame|runkodi|stop|shutdown|reboot|wakeup|rungame)
      log "Evénement reçu : $EVENT"
      ;;
    *)
      log "Événement '$EVENT' ignoré."
      continue
      ;;
  esac

  if [ ! -f "$STATE_FILE" ]; then
    log "Erreur : $STATE_FILE introuvable."
    continue
  fi

  # Extraction des données
  ACTION=$(get_val "Action")
  SYSTEM_ID=$(get_val "SystemId")
  SYSTEM_NAME=$(get_val "System")
  GAME_NAME=$(get_val "Game")
  ROM=$(get_val "GamePath")
  GAME_GENRE=$(get_val "Genre")
  GAME_GENRE_ID=$(get_val "GenreId")

  # si le nom du jeu commence par 3 chiffres puis espace, alors on les retire :
  GAME_NAME="${GAME_NAME/#[0-9][0-9][0-9] /}"
  STATUS="ON"

  # Filtrage selon les événements :
  # -
  case "$ACTION" in
    start|systembrowsing|endgame)
      clear_game
      ;;
    runkodi)
      clear_game
      SYSTEM_NAME="Kodi";
      ;;
    stop|shutdown|reboot)
      STATUS="OFF"; clear_game; SYSTEM_NAME="null"
      ;;
    wakeup|rungame)
      ;;
    *)
      log "Ignoring command \"$ACTION\" !"
      continue # On ignore les autres types d'événements
      ;;
  esac

  # 4. Construction du JSON
  IMAGE_PATH="null"
  if [ -n "$ROM" ] && [ "$ROM" != "null" ]; then
    ROM_ENC="${ROM//\//%2F}"
    ROM_ENC="${ROM_ENC// /%20}"
    IMAGE_PATH="\"api/systems/$SYSTEM_ID/roms/metadata/image/$ROM_ENC\""
  fi

  JSON_PAYLOAD=$(cat <<EOF
{
  "game": $(clean_json_val "$GAME_NAME"),
  "console": $(clean_json_val "$SYSTEM_NAME"),
  "rom": $(clean_json_val "$ROM"),
  "genre": $(clean_json_val "$GAME_GENRE"),
  "genreId": $(clean_json_val "$GAME_GENRE_ID"),
  "imagePath": $IMAGE_PATH,
  "recalboxIpAddress": $(clean_json_val "$IP_LOCALE"),
  "recalboxVersion": $(clean_json_val "$RECALBOX_VERSION"),
  "hardware": $(clean_json_val "$HARDWARE_MODEL"),
  "scriptVersion": "$SCRIPT_VERSION",
  "status": "$STATUS"
}
EOF
)

  # Vérifier/Récupérer l'IP si on ne l'a pas encore
  update_ha_ip

  # Si toujours pas d'IP, on ignore l'événement pour l'instant
  if [ -z "$HA_IP" ]; then
    log "Message non envoyé. En attente du réseau/mDNS..."
    continue
  fi

  # Arrivés ici, on a du réseau et on a récupéré l'IP de Home Assistant

  # 5. Envoi
  send_mqtt "game" "$JSON_PAYLOAD" "true"

done