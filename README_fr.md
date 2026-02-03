# Intégration Recalbox Home Assistant

<small>Par Aurélien Tomassini, 2026</small>

🇫🇷 Version Française  
[🇺🇸 Go to English version](README.md)

<img src="logo.png" height="196px">

Ce dépôt vous permet d'intégrer Recalbox dans votre Home Assistant :
- Dans votre tableau de bord :
  - Voir le status
  - Afficher le jeu en cours
  - Arrêter le jeu
  - Prendre une capture d'écran
  - Pause/reprendre l'émulateur
  - Enregistrer/charger la partie
  - Eteindre
  - Redémarrer
  - etc
- Déclencher vos automatisations.  
  Par exemple, changer la couleur des lumières selon le jeu lancé, envoyer des notifications, etc.
- Commandes vocales/textuelles Assist (EN/FR) :
  - Lancer un jeu par son titre (complet ou partiel)
  - Demander quel est le jeu en cours
  - Arrêter le jeu en cours
  - Demander une capture d'écran
  - Pause/reprendre le jeu
  - Enregistrer/charger la partie
  - Eteindre la Recalbox
  - etc

![](docs/RecalboxHomeAssistantIntegration.png)

<!-- Use "markdown-toc -i README.md --maxdepth 4" to auto update table of content -->
<!-- (if not installed yet, run "npm install --save markdown-toc -g") -->

<!-- toc -->

- [Pré-requis](#pre-requis)
- [Architecture](#architecture)
  * [Recalbox vers Home Assistant](#recalbox-vers-home-assistant)
  * [Home Assistant vers Recalbox](#home-assistant-vers-recalbox)
- [Installation](#installation)
- [Utilisation](#utilisation)
  * [Carte du Dashboard](#carte-du-dashboard)
  * [Automatisations](#automatisations)
  * [Assist (texte/voix)](#assist-textevoix)
    + [Get current game](#get-current-game)
    + [Lancer un jeu](#lancer-un-jeu)
    + [Arrêter le jeu en cours](#arreter-le-jeu-en-cours)
    + [Pause/Reprendre le jeu](#pausereprendre-le-jeu)
    + [Faire une capture d'écran](#faire-une-capture-decran)
    + [Enregistrer la partie](#enregistrer-la-partie)
    + [Charger la partie](#charger-la-partie)
    + [Turn OFF recalbox](#turn-off-recalbox)
- [Notes de versions](#notes-de-versions)
- [Aides](#aides)
  * [Problème de lancement du script Recalbox, à cause du `CRLF` / `LF`](#probleme-de-lancement-du-script-recalbox-a-cause-du-crlf--lf)

<!-- tocstop -->

## Pré-requis

- Vous devez disposer d'au moins une `Recalbox` connectée au réseau.  
  Testé pour le moment seulement sur Recalbox <mark>9.2.3</mark>, sur Raspberry Pi 3 B+.  
  Vous devez disposer du "hostname" pour accéder à la Recalbox sur le réseau, via `recalbox.local` par example.  
  > Ses ports pour l'API (80 et 81) et ports UDP (1337 et 55355) doivent être accessibles et ouverts sur le réseau local (ce qui est le cas par default sur le Recalbox).


- Vous devez disposer d'un `Home Assistant`.  
  Testé sur Home Assistant <mark>2026.1</mark>, <mark>2026.2</mark>, sur Raspberry Pi 3 B+.  
  Doit être sur le même réseau, accessible par défaut via `homeassistant.local`


## Architecture

![](docs/RecalboxHomeAssistantArchitecture.png)

### Recalbox vers Home Assistant

Sur la Recalbox, un script écoute les événements locaux, selon la documentation [Scripts sur événements d'EmulationStation | Recalbox Wiki](https://wiki.recalbox.com/fr/advanced-usage/scripts-on-emulationstation-events) .
Le script lit les informations nécessaire sur le jeu et la Recalbox, et envoie un message MQTT à Home Assistant en JSON.
Home Assistant va alors mettre à jour son entité "Recalbox" avec les informations reçues.

> Les attributs reçus par Home Assistant (dans le JSON) sont :
> - `game`
> - `console`
> - `rom`
> - `genre`
> - `genreId`
> - `imageUrl`
> - `recalboxIpAddress`
> - `recalboxVersion` : Version de l'OS Recalbox
> - `hardware` : Appareil sur lequel tourne Recalbox
> - `scriptVersion` : Version du script d'intégration sh qui tourne sur la Recalbox

### Home Assistant vers Recalbox

Depuis Home Assistant, les ordre sont envoyés à la Recalbox par API et commandes UDP :
- Commandes d'extinction, redémarrage, ou capture d'écran par API
- Liste des jeux d'une console par API
- Lancer un jeu par commande UDP

Les intégration des phrases Assist pour le texte/ la voix ont aussi été implémentés
pour le contrôle, la demande d'informations, ou cherche le jeu à lancer. Les commandes
lancées par Assist utilisent les mêmes commandes que listées ci-dessus.



## Installation

1. **Recalbox**
   
   - Copiez le script `sh` dans le dossier `userscripts` de la Recalbox. **Uniquement l'un des deux, pas les deux!**
     - `Recalbox/userscripts/home_assistant_notifier.sh` : script appelé pour chaque événement. Optimisé depuis la version v1.3.1
     - **(EXPERIMENTAL)** `Recalbox/userscripts/home_assistant_notifier(permanent).sh` : script permanent, lancé en background, qui boucles sur les événements reçus. Expérimental, pas encore au point !  
     
     Les deux scripts réagissent aux mêmes événements.
     
     > Si votre Home Assistant est accessible par un autre hôte que `homeassistant.local`,
     > changez la variable "HOME_ASSISTANT_DOMAIN" en haut du script.


2. **Home Assistant**
 
   - Installer le broker MQTT  
     
     - Créez un utilisateur Home Assistant, appelé "recalbox" (ou autre), autorisé à se connecter seulement sur le réseau local.
       Cet utilisateur sera utilisé pour l'authentification MQTT. Remplacez le login/password dans `home_assistant_notifier.sh`, lignes 13 et 14 (`MQTT_USER` & `MQTT_PASS`)
   
     - Installez le broker MQTT Mosquitto dans Home assistant (via Addons).  
       [![Open your Home Assistant instance and open install MQTT.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=mqtt)  
       Autoriser le lancement au démarrage, et activez le watchdog.
   
     - Dans les services, ajouter une intégration MQTT qui devrait maintenant être disponible.
       Cliquez sur reconfigurer, et utiliser les login/mot de passe définis au dessus.
       Assurez-vous qu'il correspondent bien à ceux dans `home_assistant_notifier.sh` lignes 13+14.
     
   - Installer Recalbox Integration
   
     - Si vous ne l'avez pas encore, installez HACS
     
     - Installez cette intégration Recalbox via ce bouton :  
       [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ooree23&repository=RecalboxHomeAssistant&category=integration)  
       Ou manuellement, ajoutez `https://github.com/ooree23/RecalboxHomeAssistant` comme dépôt, de type Integration.
       Cliquez sur télécharger, et acceptez de redémarrer.
       Cela ajoutera l'intégration Recalbox dans votre Home Assistant
       (la nouvelle intégration "Recalbox" sera visible seulement après le redémarrage, dans le menu Appareils & Service).
      
     - Ajouter une nouvelle Recalbox avec ce simple bouton :  
       [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=recalbox)  
       Ou, manuellement, allez dans le menu Appareils & Services, "+ add integration", et recherchez "Recalbox".
       Un formulaire vous demandera l'Hôst/IP de votre Recalbox (par défaut "recalbox.local"), et les ports par défaut peuvent être changés si besoin.
       Si votre Recalbox est allumée, activez "Test connection" pour valider vos paramètres.  
       
       > Vous pouvez avoir plusieurs Recalbox sur votre réseau, et dans cette intégration Home Assistant.  
       > Selon votre infrastructure, vous aurez probablement des adresses IP dynamiques : veuillez donc utiliser les noms d'hôtes,
       > différents, au lieu des adresses IP, puisque celles-ci peuvent changer dans le temps.




## Utilisation 


> La plupart des actions sur les jeux utilisent des commandes UDP.  
> Si ça ne fonctionne pas, assurez-vous que les paramètres de Recalbox ont `network_cmd_enable = true` dans `retroarch.cfg`, comme [documenté dans le Wiki Recalbox / GPIO](https://wiki.recalbox.com/en/tutorials/network/send-commands-to-emulators-with-gpio).  
> Cette version utilise le port 55355 pour les commandes UDP retroarch par defaut.


### Carte du tableau de bord

Vous pouvez ajouter une carte Recalbox à votre tableau de bord Home Assistant, pour afficher le status de la Recalbox, des jeux, l'image du jeu, etc.  
L'affichage s'actualise en temps réel.

Allez dans votre tableau de bord, en mode édition, et cliquez sur "+ ajouter carte" ; scrollez tout en bas dans les Custom Cards : "Recalbox Card".  
Depuis la version v1.3.0, une interface avec un formulaire vous aide à paramétrer la carte à vos gouts :
![](docs/RecalboxCardVisualEditor.png)

L'éditeur et la carte sont traduites en Anglais et en Français, selon la langue de votre profile Home Assistant.  
Une fois configuré, vous verrez votre carte Recalbox telle que configurée.  
Exemple : tous les boutons visibles, alerte de mises à jour activées, afficher le genre du jeu, mais cacher le chemin de la rom :

![](docs/example.png)


### Automatisations

You can also create automations, triggered when a game is launched for example.  
If interested in this example, copy [recalbox_automations.yaml](Home%20Assistant/automations/recalbox_automations.yaml) into `/config/automations/recalbox_automations.yaml`
and then add
```yaml
automation: !include automations.yaml
automation yaml: !include_dir_merge_list automations/
```
in `configuration.yaml`, to allow Home Assistant to read yaml files in `automations` subfolder.


### Assist (texte/voix)

> Since v0.2.0, a script auto installs the sentences and sentences updates.
> Check the dashboard custom card to see if the HA needs a restarts to update the sentences.


#### Get current game

Examples :
  - "What's the current game on Recalbox?"
  - "Which game is running on the Recalbox?"
  - "Quel est le jeu en cours [sur recalbox]"
  - "A quoi je joue [sur recalbox]"
  - "Qu'est-ce qui tourne sur la recalbox"
  - "Quel jeu est lancé [sur recalbox]"
  - "Quel est le jeu lancé [sur recalbox]"

![](docs/currentGameAssist.png)


#### Lancer un jeu

Examples :
  - "Launch Sonic 3 on megadrive"
  - "Run Final Fantasy on Playstation"
  - "Start Mario on Nintendo 64 on Recalbox"
  - "Play Mario on Nintendo 64 on Recalbox"
  - "Recalbox lance Pokemon Jaune sur Game Boy"
  - "Recalbox lance Mario 64 sur nintendo 64"
  - "Joue à Mario 64 sur la Nintendo 64 sur Recalbox"
  - "Lance Mario 64 sur la Nintendo 64"
  - "Lance Sonic 1 sur megadrive"

  ![](docs/launchGame.png)

> The search ignores case, and can find roms with words in between your search.
> Example : Searching for "Pokemon Jaune", can find the rom "Pokemon - Version Jaune - Edition Speciale Pikachu".


#### Arrêter le jeu en cours


Examples :
  - "Quit the current game"
  - "Stop the game on Recalbox"
  - "Arrête le jeu en cours sur Recalbox"



#### Pause/Reprendre le jeu


Examples :
  - "Pause the current game"
  - "Resume the game on Recalbox"
  - "Mets le jeu en pause"


#### Faire une capture d'écran

You can make a game screenshot, simply pushing the screenshot button on your dashboard.  
You can also make a screenshot via Assist. 

Examples :
  - "Take a screenshot of the game"
  - "Make a game screen shot"
  - "Prends une capture d'écran du jeu"
  - "Fais un screenshot du jeu"

> We try doing the screenshot in two ways :
> - trying first a UDP command screenshot, which is more integrated
> - if fails because of wrong port, then it tries using API.  
>   Note about API : on Recalbox 9.2.3 or Raspberry Pi 3, the screenshots via API are broken (also in the Recalbox Web Manager). That's why I chose UDP first.


#### Enregistrer la partie

Examples :
- "Save the current game"
- "Save my game state on Recalbox"
- "Enregistre la partie en cours"
- "Enregistre mon jeu"
- "Sauvegarde ma partie"


#### Charger la partie

Examples :
- "Load my last game state"
- "Load the last save"
- "Recharge ma sauvegarde du jeu"
- "Recharge la dernière partie"


#### Turn OFF recalbox

> This uses the Home Assistant intent to turn OFF the Recalbox, recognized as a switch.
> Please ensure that you give an easy name of your Recalbox Entity, to help
> Home Assistant Assist to recognize the device you want to turn OFF.

Examples :
- "Turn off Recalbox"
- "Eteins Recalbox"



## Notes de versions

Consultez [le fichier des notes de versions](CHANGELOG.md)


## Aides

### Problème de lancement du script Recalbox, à cause du `CRLF` / `LF` 
If your Recalbox doesn't seem to reach Home Assistant, while you have your script in `userscripts`,
please make sure the `.sh` file is using "LF" line separator :
- You can run via SSH `sh <path-to-the-script>` :  
  if there are errors saying "\r" is invalid, it means
  your sh file line separators have been modified, while it must not.
- Or you can simply open the .sh file in a compatible editor, like your IDE, or Notepad++,
  and check on the bottom right corner if it is shown `CRLF` (wrong) or `LF` (good).  

If you downloaded the file with git on windows, the line separator could have been automatically 
changed to CRLF, while Recalbox script only accepts LF.
In that case, type `git config --global core.autocrlf input` in command line, to make sure that 
git keeps the "LF" as it was in the file, without changing it.

Also, make sure that you are using the latest script version.
If your script version is too old, a message will be shown in your Recalbox Card.