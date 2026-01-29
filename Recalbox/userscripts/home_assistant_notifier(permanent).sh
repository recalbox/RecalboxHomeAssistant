#!/bin/bash

# Script : https://wiki.recalbox.com/fr/advanced-usage/scripts-on-emulationstation-events
# A placer dans le dossier userscripts
# Par Aurélien Tomassini

# Configuration
HOME_ASSISTANT_DOMAIN="homeassistant.local"
MQTT_USER="recalbox"
MQTT_PASS="recalpass"
TOPIC="recalbox/notifications"
# Chemin du fichier d'état Recalbox
STATE_FILE="/tmp/es_state.inf"

# logs
LOG_FILE="/recalbox/share/saves/home_assistant_notifier.log"
exec > "$LOG_FILE" 2>&1 # Redirige les sorties vers le fichier

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
  if [ -z "$HA_IP" ]; then
    # On vérifie si le réseau est là en tentant une résolution
    HA_IP=$(avahi-resolve -n "$HOME_ASSISTANT_DOMAIN" -4 | cut -f2)
    if [ -n "$HA_IP" ]; then
      echo "Home Assistant accessible via $HA_IP" >&2
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
  echo "Message MQTT envoyé à $HA_IP, sur $TOPIC/$sub_topic : $message" >&2
}



#------ Contournement du MQTT -------
wait_for_file_updated() {
  local file="$1"
  local last_mod
  last_mod=$(stat -t "$file" 2>/dev/null)

  while true; do
    local current_mod
    current_mod=$(stat -t "$file" 2>/dev/null)

    # Si la date a changé, on sort de la fonction
    if [ "$current_mod" != "$last_mod" ]; then
      echo "STATEFILE has been updated ! Simulating an event in 0.2 sec." >&2
      # Petit délai pour laisser Recalbox finir d'écrire le fichier
      sleep 0.2
      return 0
    fi

    # On attend 1 seconde avant la prochaine vérification pour économiser le CPU
    sleep 1
  done
}



#----- Script permanent -----
# Voir si le script tourne :      ps auxw | grep "assistant"
# Lancer le script à la main :    bash -x "/recalbox/share/userscripts/home_assistant_notifier(permanent).sh"
# générer un événement fake:      mosquitto_pub -h 127.0.0.1 -t "/Recalbox/EmulationStation/Event" -m "start"
# voir les logs de cet outil:     tail -f "/recalbox/share/saves/home_assistant_notifier.log"

echo "Démarrage du démon de notification Home Assistant par MQTT..." >&2
ALLOWED_EVENTS="start|systembrowsing|endgame|runkodi|stop|shutdown|reboot|wakeup|rungame"

while true; do

  # Débloquer avec
  # mosquitto_pub -h 127.0.0.1 -t "/Recalbox/EmulationStation/Event" -m "start"
  # pour déclencher un événement MQTT
  echo "En attente d'un nouvel événement..." >&2
  EVENT=$(mosquitto_sub -h "$MQTT_LOCAL_HOST" -p $MQTT_LOCAL_PORT -q 0 -t "$TOPIC_LOCAL" -C 1)

  case "$EVENT" in
    $ALLOWED_KEYS)
      echo "Evénement reçu : $EVENT" >&2
      ;;
    *)
      echo "Événement '$EVENT' ignoré." >&2
      continue
      ;;
  esac

  # Arrivés ici, on a du réseau et on a récupéré l'IP de Home Assistant

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
      SYSTEM_NAME="Kodi"; GAME_NAME="Lecteur multimédia"
      ;;
    stop|shutdown|reboot)
      STATUS="OFF"; clear_game; SYSTEM_NAME="null"
      ;;
    wakeup|rungame)
      ;;
    *)
      echo "! Ignoring command \"$ACTION\" !"
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
  "recalboxVersion": $(clean_json_val "$RECALBOX_VERSION"),
  "hardware": $(clean_json_val "$HARDWARE_MODEL")
}
EOF
)

  # Vérifier/Récupérer l'IP si on ne l'a pas encore
  update_ha_ip

  # Si toujours pas d'IP, on ignore l'événement pour l'instant
  if [ -z "$HA_IP" ]; then
    echo "Message non envoyé. En attente du réseau/mDNS..." >&2
    continue
  fi

  # 5. Envoi
  send_mqtt "status" "$STATUS" "false"
  send_mqtt "game" "$JSON_PAYLOAD" "true"

done