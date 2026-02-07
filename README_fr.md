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
  * [Carte du tableau de bord](#carte-du-tableau-de-bord)
  * [Automatisations](#automatisations)
  * [Assist (texte/voix)](#assist-textevoix)
    + [Savoir quel est le jeu en cours](#savoir-quel-est-le-jeu-en-cours)
    + [Lancer un jeu](#lancer-un-jeu)
    + [Arrêter le jeu en cours](#arreter-le-jeu-en-cours)
    + [Pause/Reprendre le jeu](#pausereprendre-le-jeu)
    + [Faire une capture d'écran](#faire-une-capture-decran)
    + [Enregistrer la partie](#enregistrer-la-partie)
    + [Charger la partie](#charger-la-partie)
    + [Eteindre la recalbox](#eteindre-la-recalbox)
    + [Quitter Kodi](#quitter-kodi)
- [Notes de versions](#notes-de-versions)
- [Aides](#aides)
  * [Problème de lancement du script Recalbox, à cause du `CRLF` / `LF`](#probleme-de-lancement-du-script-recalbox-a-cause-du-crlf--lf)
  * [IP v6](#ip-v6)

<!-- tocstop -->

## Pré-requis

- Vous devez disposer d'au moins une `Recalbox` connectée au réseau.  
  Testé pour le moment seulement sur Recalbox <mark>9.2.3</mark>, sur Raspberry Pi 3 B+.  
  Vous devez disposer du "hostname" pour accéder à la Recalbox sur le réseau, via `recalbox.local` par example.  
  > Ses ports pour l'API (80 et 81) et ports UDP (1337 et 55355) doivent être accessibles et ouverts sur le réseau local (ce qui est le cas par default sur la Recalbox).


- Vous devez disposer d'un `Home Assistant` sur le réseau.  
  Testé sur Home Assistant <mark>2026.1</mark>, <mark>2026.2</mark>, sur Raspberry Pi 3 B+.  
  Doit être sur le même réseau, accessible par défaut via `homeassistant.local`


## Architecture

![](docs/RecalboxHomeAssistantArchitecture.png)

### Recalbox vers Home Assistant

Sur la Recalbox, un script écoute les événements locaux, selon la documentation [Scripts sur événements d'EmulationStation | Recalbox Wiki](https://wiki.recalbox.com/fr/advanced-usage/scripts-on-emulationstation-events) .
Le script lit les informations nécessaires sur le jeu et la Recalbox, et envoie un message à Home Assistant au format JSON.
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

Les intégrations des phrases Assist pour le texte/ la voix ont aussi été implémentés
pour le contrôle, la demande d'informations, ou cherche le jeu à lancer. Les commandes
lancées par Assist utilisent les mêmes commandes que listées ci-dessus.



## Installation

1. **Recalbox**
   
   - Copiez le script `Recalbox/userscripts/home_assistant_notifier.sh` dans le dossier `userscripts` de la Recalbox. Optimisé depuis la version v1.3.1.
     
     > Si votre Home Assistant est accessible par un autre hôte que `homeassistant.local`,
     > changez la variable "HOME_ASSISTANT_DOMAIN" en haut du script.


2. **Home Assistant**
   
   - Si vous ne l'avez pas encore, [installez HACS](https://www.hacs.xyz/docs/use/download/download/)
   
   - Installez cette **intégration Recalbox** via ce bouton :  
     [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ooree23&repository=RecalboxHomeAssistant&category=integration)  
     > Ou manuellement, ajoutez `https://github.com/ooree23/RecalboxHomeAssistant` comme dépôt, de type Integration.
       Cliquez sur télécharger, et acceptez de redémarrer.
     
     Cela ajoutera l'intégration Recalbox dans votre Home Assistant
     (la nouvelle intégration "Recalbox" sera visible seulement après le redémarrage, dans le menu Appareils & Service).
    
   - Ajouter une **nouvelle Recalbox** avec ce simple bouton :  
     [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=recalbox)  
     > Ou, manuellement, allez dans le menu Appareils & Services, "+ add integration", et recherchez "Recalbox".
     
     Un formulaire vous demandera l'Hôst/IP de votre Recalbox (par défaut "recalbox.local"), et les ports par défaut peuvent être changés si besoin.
     Si votre Recalbox est allumée, activez "Test connection" pour valider vos paramètres.  

     ![](docs/DeviceIntegrationSelectAndConfig.png)

     > Vous pouvez avoir plusieurs Recalbox sur votre réseau, et dans cette intégration Home Assistant.  
       Selon votre infrastructure, vous aurez probablement des adresses IP dynamiques : veuillez donc utiliser les noms d'hôtes,
       différents, au lieu des adresses IP, puisque celles-ci peuvent changer dans le temps.




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

> Démonstration : https://youtu.be/H2Tp9kacX0E?si=-ZFEbC_dkr6CJ-ky

Vous pouvez créer des automatisations, déclenchées par exemple lorsqu'un jeu est lancé.  
Si cet exemple vous intéresse, copiez [recalbox_automations.yaml](Home%20Assistant/automations/recalbox_automations.yaml) dans `/config/automations/recalbox_automations.yaml`
puis ajoutez
```yaml
automation: !include automations.yaml
automation yaml: !include_dir_merge_list automations/
```
dans `configuration.yaml`, pour permettre à Home Assistant de lire les fichiers yaml du dossier `automations`.


### Assist (texte/voix)

> Démonstration : https://youtube.com/shorts/TIOIKZNCbBE?si=my2BR19OPJmfDUWc

> Depuis la version v0.2.0, un script va automatiquement installer les phrases Assist au bon endroit, et ses mises à jour.
> Vérifiez la carte du tableau de bord si un redémarrage manuel est nécessaire.


#### Savoir quel est le jeu en cours

Exemples :
  - "What's the current game on Recalbox?"
  - "Which game is running on the Recalbox?"
  - "Quel est le jeu en cours [sur recalbox]"
  - "A quoi je joue [sur recalbox]"
  - "Qu'est-ce qui tourne sur la recalbox"
  - "Quel jeu est lancé [sur recalbox]"
  - "Quel est le jeu lancé [sur recalbox]"

![](docs/currentGameAssist.png)


#### Lancer un jeu

Exemples :
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

> La recherche est insensible à la casse, et peut trouver des roms ayant des mots entre vos termes.
> Exemple : Si vous recherchez "Pokemon Jaune", on peut trouver la rom "Pokemon - Version Jaune - Edition Speciale Pikachu".


#### Arrêter le jeu en cours


Exemples :
  - "Quit the current game"
  - "Stop the game on Recalbox"
  - "Arrête le jeu en cours sur Recalbox"



#### Pause/Reprendre le jeu


Exemples :
  - "Pause the current game"
  - "Resume the game on Recalbox"
  - "Mets le jeu en pause"


#### Faire une capture d'écran

Vous pouvez faire un screenshot en cliquant simplement sur le bouton correspondant sur le tableau de bord.  
Vous pouvez aussi faire un screenshot par une demande sur Assist. 

Exemples :
  - "Take a screenshot of the game"
  - "Make a game screen shot"
  - "Prends une capture d'écran du jeu"
  - "Fais un screenshot du jeu"

> On essaye de faire la capture de deux moyens :
> - d'abord par une commande UDP, qui est mieux intégrée
> - en cas d'échec (mauvais port?), alors on essaye par un appel à l'API.  
>   Note à propos de l'API : sur Recalbox 9.2.3 sur Raspberry Pi 3, la capture par l'API donne des images "cassées" (tout comme par le Web Manager Recalbox). C'est pour cela qu'on essaye d'abord la version UDP.


#### Enregistrer la partie

Exemples :
- "Save the current game"
- "Save my game state on Recalbox"
- "Enregistre la partie en cours"
- "Enregistre mon jeu"
- "Sauvegarde ma partie"


#### Charger la partie

Exemples :
- "Load my last game state"
- "Load the last save"
- "Recharge ma sauvegarde du jeu"
- "Recharge la dernière partie"


#### Eteindre la recalbox

> Cet ordre utilise les intentions natives de Home Assistant, pour éteindre la Recalbox, reconnue comme un interrupteur.
> Assurez-vous donc d'avoir donné un nom prononçable à votre entité Recalbox, pour faciliter la compréhension par
> Home Assistant de quel objet vous voulez éteindre.

Exemples :
- "Turn off Recalbox"
- "Eteins Recalbox"


#### Quitter Kodi

> Utilise le port 8081 par defaut. Fonctionne uniquement si Kodi est lancé.

Exemples :
- "Quitte Kodi"
- "Ferme Kodi"



## Notes de versions

Consultez [le fichier des notes de versions](CHANGELOG.md)


## Aides

### Problème de lancement du script Recalbox, à cause du `CRLF` / `LF`

Si votre Recalbox ne semble pas communiquer avec Home Assistant alors que
votre script est bien présent dans userscripts, veuillez vous assurer que le fichier `.sh`
utilise le séparateur de ligne "LF" :

- Vous pouvez tester via SSH en lançant `sh <path-to-the-script>` :  
  si des erreurs indiquent que "\r" est invalide,
  cela signifie que les séparateurs de ligne de votre fichier ont été
  modifiés, ce qui ne doit pas arriver.
- Vous pouvez aussi simplement ouvrir le fichier `.sh` dans un éditeur compatible,
  comme votre IDE ou Notepad++, et vérifier dans le coin inférieur droit s'il affiche
  `CRLF` (incorrect) ou `LF` (correct).

Si vous avez téléchargé le fichier via Git sous Windows, le séparateur de ligne a pu être automatiquement
remplacé par CRLF, alors que le script Recalbox n'accepte que le LF.
Dans ce cas, tapez `git config --global core.autocrlf input` dans votre terminal,
pour vous assurer que Git conserve le format "LF" d'origine sans le modifier.

Enfin, assurez-vous d'utiliser la dernière version du script.
Si votre version est trop ancienne, un message s'affichera sur votre carte Recalbox dans Home Assistant.



### IP v6

Quand Home Assistants résout le hostname de votre Recalbox, il peut obtenir une IPv6.
Il peu parfois y avoir des problème avec les IPv6 (au moins sur RPi3), et la Recalbox ne reçoit donc pas les requêtes de Home Assistant.
Un message apparait en bas de l'écran de Home Assistant, montrant une adresse IPv6.

Si cela se produit et vous bloque :
- depuis la v1.5.4, une option vous permet d'essayer le forcing de la résolution mDNS en IP v4
  ![](docs/force_ipv4_resolution.png)
- si cela ne suffit pas, essayez de désactiver l'IP v6 sur Home Assistant (Paramètres, Réseau, IPv6, désactiver)
- si ça ne suffit toujours pas, mettez l'IP de votre Recalbox au lieu du nom d'hôte dans les paramètres de l'intégration personnalisée

Related HA issues :
- https://github.com/home-assistant/core/issues/161174
- https://github.com/home-assistant/core/issues/161877
