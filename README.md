# Recalbox Home Assistant integration

<small>By Aurélien Tomassini, 2026</small>

<img src="logo.png" height="196px">

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
- Voice/text commands with assistant (EN/FR) :
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
    + [Pause/Resume the current game](#pauseresume-the-current-game)
    + [Take a screenshot](#take-a-screenshot)
    + [Turn OFF recalbox](#turn-off-recalbox)
- [Releases notes](#releases-notes)

<!-- tocstop -->

## Requirements

- You should have a `Recalbox` OS available.  
  Tested only with Recalbox <mark>9.2.3</mark>, Raspberry Pi 3 B+.  
  By default, should be accessible on `recalbox.local`.  
  > Its API ports (80 and 81) and UDP ports (1337 and 55355) should be accessible in the local network (enabled by default).


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
 
   - Install MQTT Broker  
     
     - Create a new Home Assistant User, named "recalbox" (or something else), allowed to connect only on the local network. This user will be used for MQTT Authentication. Replace the user/password `home_assistant_notifier.sh` line 13 and 14 (`MQTT_USER` & `MQTT_PASS`)
   
     - Install MQTT Mosquitto broker in Home assistant (in addons).  
       [![Open your Home Assistant instance and open install MQTT.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=mqtt)  
       Enable the Run on start, and watchdog.
   
     - In services integration, add MQTT service which should be now available.
       Click on reconfigure, and use the credentials defined for authentication.
       Double check they are the same defined in `home_assistant_notifier.sh` lines 13+14.
     
   - Install Recalbox Integration
   
     - If not installed yet, install HACS
     
     - Install this repository via this button :  
       [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ooree23&repository=RecalboxHomeAssistant&category=integration)  
       Or manually, add `https://github.com/ooree23/RecalboxHomeAssistant` as repository, as Integration.
       Press download, and then accept to restart.
       It will automatically add Recalbox integration to your Home Assistant
       (new "Recalbox" Integration will be available after restart in the Devices & Service menu).
      
     - Go to Devices & Services menu, "+ add integration", and search for "Recalbox".
       Add the IP of your Recalbox, or let the default "recalbox.local".
       
       > A second reboot could be necessary, depending on what's shown on dashboard custom card,
       > to apply the newly installed custom_sentences for Assist.

      


## Usage 


> Most of actions features use UDP commands.  
> It requires to set `network_cmd_enable = true` in `retroarch.cfg`, as [documented in the Recalbox Wiki / GPIO](https://wiki.recalbox.com/en/tutorials/network/send-commands-to-emulators-with-gpio).  
> Please double check the port configured in your device : this versions uses port 55355 for retroarch UDP commands.


### Dashboard card

You can add a Recalbox card to your Home Assistant dashboard, in order to display the Recalbox status, game info, picture, etc.  
It will be refreshed in real time.

Go to your dashboard in edit mode, "+ add card", scroll down to Custom Cards : "Recalbox Card".
Fill the yaml :
```yaml
type: custom:recalbox-card
entity: switch.recalbox_recalbox_local
```
And you will get this (in French or English, depending on your user language)

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


#### Launch a game

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


#### Stop the current game


Examples :
  - "Quit the current game"
  - "Stop the game on Recalbox"
  - "Arrête le jeu en cours sur Recalbox"



#### Pause/Resume the current game


Examples :
  - "Pause the current game"
  - "Resume the game on Recalbox"
  - "Mets le jeu en pause"


#### Take a screenshot

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


#### Turn OFF recalbox

> This uses the Home Assistant intent to turn OFF the Recalbox, recognized as a switch.
> Please ensure that you give an easy name of your Recalbox Entity, to help
> Home Assistant Assist to recognize the device you want to turn OFF.

Examples :
- "Turn off Recalbox"
- "Eteins Recalbox"



## Releases notes

See [change logs file](CHANGELOG.md)
