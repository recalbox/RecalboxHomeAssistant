# Recalbox Home Assistant integration

> By Aurélien Tomassini, 2026.

This repository allows you to integrate Recalbox in your Home Assistant :
- In your dashboard :
  - Get status
  - Display current game
  - Turn off
  - Reboot
  - Take screenshots
  - etc
- Trigger any automation you want.  
  For example, change light color according to the game launched, send notifications, etc.
- Voice/text commands with assistant :
  - Launch a game by its title (full or partial title search)
  - Ask what is the current game
  - Stop current game
  - Take a screenshot
  - Turn off Recalbox
  - etc

![](docs/RecalboxHomeAssistantIntegration.png)

<!-- Use "markdown-toc -i README.md --maxdepth 4" to auto update table of content -->
<!-- (if not installed yet, run "npm install --save markdown-toc -g") -->

<!-- toc -->

- [Requirements](#requirements)
- [Architecture](#architecture)
  * [Recalbox to Home Assistant](#recalbox-to-home-assistant)
  * [Home Assistant to Recalbox](#home-assistant-to-recalbox)
- [Installation](#installation)
- [Usage](#usage)
  * [Dashboard card](#dashboard-card)
  * [Automations](#automations)
  * [Assist (text/voice)](#assist-textvoice)
    + [Get current game](#get-current-game)
    + [Launch a game](#launch-a-game)
    + [Stop the current game](#stop-the-current-game)
    + [Take a screenshot](#take-a-screenshot)
- [Releases notes](#releases-notes)

<!-- tocstop -->

## Requirements

- You should have a `Recalbox` OS available.  
  Tested only with Recalbox <mark>9.2.3</mark>, Raspberry Pi 3 B+.  
  By default, should be accessible on `recalbox.local`


- You should have a `Home Assistant`.  
  Tested on Home Assistant <mark>2026.1</mark>, Raspberry Pi 3 B+.  
  By default, It should be accessible in the same network, at `homeassistant.local`


## Architecture

![](docs/RecalboxHomeAssistantArchitecture.png)

### Recalbox to Home Assistant

On the Recalbox, a script listens on local events, based on [Scripts sur événements d'EmulationStation | Recalbox Wiki](https://wiki.recalbox.com/fr/advanced-usage/scripts-on-emulationstation-events) .
The scripts reads the needed data for game information, and sends a MQTT message to Home Assistant with JSON data.
Home Assistant can then update its "Recalbox" entity with the current game.

> The attributes read by Home Assistant are, through this JSON :
> - `game `: name of the running game, user friendly. null if no game launched.
> - `console `: name of the console, user friendly. null if no game launched, or "Kodi"
> - `rom `: path to the current rom. null if no game launched.
> - `genre `: genre of the running game, user friendly. null if no game launched.
> - `genreId `: genreId of the running game. null if no game launched. Can be useful for automation where you want to set lights colors depending on type of game for example.
> - `imageUrl `: URL to the image of the current game. null if no game running. The picture exists only if the game has been scrapped.
> - `recalboxVersion` : Version of the Recalbox OS
> - `hardware` : Device running the Recalbox

### Home Assistant to Recalbox

On Home Assistant, orders are sent to Recalbox via API and UDP commands :
- Stop, reboot, screenshot commands via API
- Game list via API
- Launch a game via UDP

Assist integration for voice/text control has also been implemented in order to
control, get information, or find a game to launch.  
It uses the same services just listed.



## Installation

1. **Recalbox**
   
   - Copy the file `Recalbox/userscripts/home_assistant_notifier.sh` in the `userscripts` Recalbox folder.
     This script will react to Recalbox events.


2. **Home Assistant**
 
   - Install MQTT Broker :
   
     - Create a new Home Assistant User, named "recalbox" (or something else), allowed to connect only on the local network. This user will be used for MQTT Authentication. Replace the user/password `home_assistant_notifier.sh` line 13 and 14 (`MQTT_USER` & `MQTT_PASS`)
   
     - Install MQTT Mosquitto broker in Home assistant (in addons). Enable the Run on start, and watchdog.
   
     - In services integration, add MQTT service which should be now available.
       Click on reconfigure, and use the credentials defined for authentication.
       Double check they are the same defined in `home_assistant_notifier.sh` lines 13+14.
     
   - Install Recalbox Integration
   
     - Install HACS, and then click below
     
     - [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=tototo23&repository=RecalboxHomeAssistant&category=integration)  
       Or manually, add `https://github.com/tototo23/RecalboxHomeAssistant` as repository, as Integration.
       Press download, and then accept to restart.
       It will automatically add Recalbox to your Home Assistant, with device creation
       (new "Recalbox" Integration will be available after restart), the custom_sentences recognition for assist, and a custom dashboard card.


## Usage 

### Dashboard card

You can add a card to your Home Assistant dashboard, in order to display the Recalbox status, game info, picture, etc.  
It will be refreshed in real time.  
Simply add to your dashboard a `"type: custom:recalbox-card"` with your Recalbox entity :
`entity: binary_sensor.recalbox_recalbox_local` (or similar)  
![](docs/example.png)


### Automations

You can also create automations, triggered when a game is launched for example.  
If interested in this example, copy [recalbox_automations.yaml](Home%20Assistant/automations/recalbox_automations.yaml) into `/config/automations/recalbox_automations.yaml`
and then add
```yaml
automation: !include automations.yaml
automation yaml: !include_dir_merge_list automations/
```
in `configuration.yaml`, to allow Home Assistant to read yaml files in `automations` subfolder.


### Assist (text/voice)

> Since Janvuary 24th, a script auto installs the sentences and sentences updates.
> Check the dashboard custom card to see if the HA needs a restarts to update the sentences.


#### Get current game

Examples :
  - "quel est le jeu en cours [sur recalbox]"
  - "à quoi je joue [sur recalbox]"
  - "qu'est-ce qui tourne sur la recalbox"
  - "quel jeu est lancé [sur recalbox]"
  - "quel est le jeu lancé [sur recalbox]"

![](docs/currentGameAssist.png)


#### Launch a game

Examples :
  - "Recalbox lance Pokemon Jaune sur Game Boy"
  - "Recalbox lance Mario 64 sur nintendo 64"
  - "Joue à Mario 64 sur la Nintendo 64 sur Recalbox"
  - "Lance Mario 64 sur la Nintendo 64"
  - "Lance Sonic 1 sur megadrive"

  ![](docs/launchGame.png)

> The search ignores case, and can find roms with words in between your search.
> Example : Searching for "Pokemon Jaune", can find the rom "Pokemon - Version Jaune - Edition Speciale Pikachu".


#### Stop the current game


Examples :
  - "Arrête le jeu en cours sur Recalbox"


> This uses a retroarch UDP command.  
> It requires to set `network_cmd_enable = true` in `retroarch.cfg`, as [documented in the Recalbox Wiki / GPIO](https://wiki.recalbox.com/en/tutorials/network/send-commands-to-emulators-with-gpio).  
> Please double check the port configured in your device : this versions uses port 55355 for retroarch UDP commands.


#### Take a screenshot

You can make a game screenshot, simply pushing the screenshot button on your dashboard.  
You can also make a screenshot via Assist. 

Examples :

  - "Prends une capture d'écran du jeu"
  - "Fais un screenshot du jeu"

> Since January 26th 2026, the screenshot is done with a script :
> - trying first a UDP command screenshot, which is more integrated
> - if fails because of wrong port, then it tries using API.  
>   Note about API : on Recalbox 9.2.3 or Raspberry Pi 3, the screenshots via API are broken (also in the Recalbox Web Manager). That's why I chose UDP first.

    

## Releases notes

See [change logs file](CHANGELOG.md)
