#!/bin/bash

# Script : https://wiki.recalbox.com/fr/advanced-usage/scripts-on-emulationstation-events
# A placer dans le dossier userscripts
# Par Aurélien Tomassini

# Configuration
HOME_ASSISTANT_DOMAIN="homeassistant.local"
RECALBOX_DOMAIN="recalbox.local"

# Récupérer l'IP via mDNS
HA_IP=$(avahi-resolve -n $HOME_ASSISTANT_DOMAIN -4 | cut -f2)
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

# si le nom du jeu commence par 3 chiifres puis espace, alors on les retire :
GAME_NAME="${GAME_NAME/#[0-9][0-9][0-9] /}"


# Nettoyage des variables pour le JSON
clean_json_val() {
    if [ -z "$1" ] || [ "$1" == "null" ]; then
        echo "null"
    else
        echo "\"$1\""
    fi
}


# Fonction pour envoyer les messages MQTT
# Usage: send_mqtt "sous_topic" "message"
send_mqtt() {
    local sub_topic="$1"
    local message="$2"
	
    if [ "$3" == "true" ]; then
		mosquitto_pub -h "$HA_IP" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$TOPIC/$sub_topic" -m "$message" -r
	else
		mosquitto_pub -h "$HA_IP" -u "$MQTT_USER" -P "$MQTT_PASS" -t "$TOPIC/$sub_topic" -m "$message"
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

case "$ACTION" in
    start|systembrowsing|endgame)
		clear_game
        ;;
    runkodi)
		clear_game
		SYSTEM_NAME="Kodi"
		GAME_NAME="Lecteur multimédia"
        ;;
    wakeup|rungame)
        ;;
    stop)
		STATUS="OFF"
		clear_game
		CONSOLE_JSON="null"
        ;;
    *)
		echo "! Ignoring command \"$ACTION\" !"
		exit 1
        ;;
esac





	
# Extraction de la version et du hardware
RECALBOX_VERSION=$(cat /recalbox/recalbox.version 2>/dev/null || echo "Inconnue")
HARDWARE_MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo "Hardware inconnu")


# Fonction pour générer le JSON de jeu
gen_game_json() {
    local imageUrl="null"
	if [ -n "$ROM" ] && [ "$ROM" != "null" ]; then
		local ROM_PATH_ENCODED="${ROM//\//%2F}"
        local ROM_PATH_ENCODED="${ROM_PATH_ENCODED// /%20}"
		imageUrl="\"http://$RECALBOX_DOMAIN:81/api/systems/$SYSTEM_ID/roms/metadata/image/$ROM_PATH_ENCODED\""
	fi
    
    cat <<EOF
{
  "game": $(clean_json_val "$GAME_NAME"),
  "console": $(clean_json_val "$SYSTEM_NAME"),
  "rom": $(clean_json_val "$ROM"),
  "genre": $(clean_json_val "$GAME_GENRE"),
  "genreId": $(clean_json_val "$GAME_GENRE_ID"),
  "imageUrl": $imageUrl,
  "recalboxVersion": $(clean_json_val "$RECALBOX_VERSION"),
  "hardware": $(clean_json_val "$HARDWARE_MODEL")
}
EOF
}


# Si on doit effacer le retain du status...
# send_mqtt "status" "" "true"
# On ne demande pas de retenir l'état sur le log terme
send_mqtt "status" "$STATUS" "false"
# Mais on veut persister les attributs, notamment pour retenir la version de recalbox et le hardware
send_mqtt "game" "$(gen_game_json)" "true"
