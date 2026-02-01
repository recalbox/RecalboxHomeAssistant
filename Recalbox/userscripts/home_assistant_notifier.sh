#!/bin/bash

# Script : https://wiki.recalbox.com/fr/advanced-usage/scripts-on-emulationstation-events
# A placer dans le dossier userscripts
# Par Aurélien Tomassini

SCRIPT_VERSION="home_assistant_notifier.sh:v1.4.0"

# Configuration
HOME_ASSISTANT_DOMAIN="homeassistant.local"
HOME_ASSISTANT_IP_CACHE_FILE="/tmp/ha_ip_address.txt"
LOGS_FOLDER="/recalbox/share/system/logs/home_assistant_integration"
#Adresse IP de Recalbox. Sera récupérée plus bas pour optimiser
HA_IP=""
MQTT_USER="recalbox"
MQTT_PASS="recalpass"
TOPIC="recalbox/notifications"
# Chemin du fichier d'état Recalbox
STATE_FILE="/tmp/es_state.inf"


# Vérification de l'existence du fichier
if [ ! -f "$STATE_FILE" ]; then
  echo "Erreur : $STATE_FILE introuvable."
  exit 1
fi

# Fonction pour extraire une valeur par sa clé
get_val() {
  # Cherche la ligne commençant par la clé, extrait ce qui est après le premier =
  grep "^$1=" "$STATE_FILE" | cut -d'=' -f2- | tr -d '\r' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

# Extraction des données
ACTION=$(get_val "Action")
GAME_NAME=$(get_val "Game")
ROM=$(get_val "GamePath")
GAME_IMAGE_PATH=$(get_val "ImagePath")
SYSTEM_ID=$(get_val "SystemId")
SYSTEM_NAME=$(get_val "System")
GAME_GENRE=$(get_val "Genre")
GAME_GENRE_ID=$(get_val "GenreId")

# si le nom du jeu commence par 3 chiffres puis espace, alors on les retire :
GAME_NAME="${GAME_NAME/#[0-9][0-9][0-9] /}"


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

# Nettoyage des variables pour le JSON
clean_json_val() {
  if [ -z "$1" ] || [ "$1" == "null" ]; then
    echo "null"
  else
    echo "\"$1\""
  fi
}


# Fonction pour envoyer les messages MQTT
# Usage: send_mqtt "sous_topic" "message" retain
send_mqtt() {
  local sub_topic="$1"
  local message="$2"
  
  if [ "$3" == "true" ]; then
    mosquitto_pub -h "$HA_IP" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$TOPIC/$sub_topic" -m "$message" -r
    log "Message MQTT (retain) envoyé à $HA_IP, sur $TOPIC/$sub_topic : $message"
  else
    mosquitto_pub -h "$HA_IP" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$TOPIC/$sub_topic" -m "$message"
    log "Message MQTT envoyé à $HA_IP, sur $TOPIC/$sub_topic : $message"
  fi
}

clear_game() {
  GAME_NAME="null"
  ROM="null"
  GAME_IMAGE_PATH="null"
  GAME_GENRE="null"
  GAME_GENRE_ID="null"
}

STATUS="ON"
prepare_logs_file

case "$ACTION" in
  start|systembrowsing|endgame)
    clear_game
    ;;
  runkodi)
    clear_game
    SYSTEM_NAME="Kodi"
    ;;
  wakeup|rungame)
    ;;
  stop|shutdown|reboot)
    STATUS="OFF"
    clear_game
    CONSOLE_JSON="null"
    ;;
  *)
    # echo "Ignoring command \"$ACTION\" !"
    exit 1
    ;;
esac


log "Generating data for received command $ACTION"


# On récupère l'IP (la première trouvée)
IP_LOCALE=$(ip -4 addr show scope global | awk '/inet / {print $2}' | cut -d/ -f1 | head -n 1)
# On vérifie si la variable est vide
if [ -z "$IP_LOCALE" ]; then
    echo "Erreur : Non connecté au réseau."
    exit 1
fi

# Chemin du cache pour l'IP
if [ -f "$HOME_ASSISTANT_IP_CACHE_FILE" ]; then
    # Récupérer l'IP via le cache
    HA_IP=$(cat "$HOME_ASSISTANT_IP_CACHE_FILE")
    log "IP récupérée du cache : $HA_IP"
else
    # Récupérer l'IP via mDNS
    HA_IP=$(avahi-resolve -n $HOME_ASSISTANT_DOMAIN -4 | cut -f2)
    if [ -n "$HA_IP" ]; then
      echo "$HA_IP" > "$HOME_ASSISTANT_IP_CACHE_FILE"
      log "IP résolue via mDNS et mise en cache : $HA_IP"
    fi
fi

# Extraction de la version et du hardware
RECALBOX_VERSION=$(cat /recalbox/recalbox.version 2>/dev/null || echo "Inconnue")
HARDWARE_MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo "Hardware inconnu")


# Fonction pour générer le JSON de jeu
gen_game_json() {
  local imagePath="null"
  if [ -n "$ROM" ] && [ "$ROM" != "null" ]; then
    local ROM_PATH_ENCODED="${ROM//\//%2F}"
    ROM_PATH_ENCODED="${ROM_PATH_ENCODED// /%20}"
    imagePath="\"api/systems/$SYSTEM_ID/roms/metadata/image/$ROM_PATH_ENCODED\""
  fi
    
  cat <<EOF
{
  "game": $(clean_json_val "$GAME_NAME"),
  "console": $(clean_json_val "$SYSTEM_NAME"),
  "rom": $(clean_json_val "$ROM"),
  "genre": $(clean_json_val "$GAME_GENRE"),
  "genreId": $(clean_json_val "$GAME_GENRE_ID"),
  "imagePath": $imagePath,
  "recalboxIpAddress": $(clean_json_val "$IP_LOCALE"),
  "recalboxVersion": $(clean_json_val "$RECALBOX_VERSION"),
  "hardware": $(clean_json_val "$HARDWARE_MODEL"),
  "scriptVersion": "$SCRIPT_VERSION",
  "status": "$STATUS"
}
EOF
}


# Si on doit effacer le retain du status...
# send_mqtt "status" "" "true"
# Mais on veut persister les attributs, notamment pour retenir la version de recalbox et le hardware
send_mqtt "game" "$(gen_game_json)" "true"
