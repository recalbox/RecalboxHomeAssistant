# Recalbox Home Assistant integration - Changelog

> By Aurélien Tomassini, 2026.

## v1.0.1 - Work in progress...

- Add a coordinator, which pings the Recalbox every 1min, to check if it is still ON
- Add HACS integration button in the Github page
- Improve logs
- Internationalisation FR/EN of the Dashboard card
- Set "Recalbox" notification channel on automation example
- Remove screenshot button when Kodi is running



## v1.0.0 - 25/01/2026 - First stable version

- Add a quit current game button, when a game is running


## v0.2.1 - 25/01/2026

- Compare MD5 of sentences files, in order to update them only when required.
  It avoids to show double restart required when the update doesn't change the sentences.



## v0.2.0 - 24/01/2026

- As `extra_folders` is not working, added a script to copy the `custom_components/recalbox/custom_sentences`
  to `custom_sentences`. As this script is launched when the integration starts, you could need two restarts
  to get Assist sentences : a first restart to run the integration, that will copy the sentences ; and a second
  restart, that will read the sentences on start.
- Display in dashboard if the secondary restart is needed.
  The alert is shown when the sentences have been changed.
- Fill the default host when creating your Recalbox, with `recalbox.local`
- Move recalbox entities to "instances" in order to be able to store other "global" variables, like "needs_restart"
  to show info in the dashboard.

 
## v0.1.2 - 24/01/2026

- Try to force HACS to copy `custom_sentences` folder, thanks to `extra_folders` key
- Improve dashboard card actions CSS to make bottom smooth


## v0.1.1 - 24/01/2026

- Deep modification to move recalbox actions in the entity, making buttons and intents only proxies
- Fix shut down with the button, to force and keep status OFF
- If an image path exists, but not the image, do not display the broken image


## v0.1.0 - 24/01/2026

- Changes from Yaml version to Python custom integration
- New screenshot script : it first tries a UDP screenshot.
  If it fails, then it tries a screenshot via API.  
  Used both for voice/text command, and button pressed.
- Update dashboard card and button icons
- Improve notify automation example, to avoid wrong notification when Home Assistant updates itself while Recalbox is still off.
- When looking for game name in game launch, remove accents
- Create HACS files to enable repo download via HACS


## v0.0.2 - 20/01/2026

- Update the example dashboard template, to use the device information to display it at the bottom of the Recalbox column
- Moved variables to be changed on top of the `recalbox.yaml` file. The version and hardware are not hardcoded anymore.
- Adds web links to recalbox web manager, and to this repository to get updates
- Try to search for a game even if the recalbox is not seen connected
- Add `recalboxVersion` and `hardware` in the MQTT message sent to Home Assistant. So HA can know the OS version and device of Recalbox.
- Update the recalbox_card example with actual Recabox version and hardware
- Recalbox now sends messages to MQTT in retain mode for the attributes (and then remember the recabox version and hardware)
- Add 2 sensors sensor.recalbox_hardware and sensor.recalbox_firmware_version to persist values
- Add screen shot button
- Add screen shot action via assist (text or voice)
- Launch game from text/voice command, searching for the ROM in the wanted system, and launch command via UDP


## v0.0.1 - 13/01/2026

> First integration

- Hardcoded device as a Recalbox 9.2.3 on Raspberry Pi 3 (no effect, only for display). It can be changed with the yaml
- Script on Recalbox side to notify the Home Assistant of any event, and compute the game image URL
- Home Assistant package configuration complete for receiving Recalbox events, actions to turn off or reboot the recabox, dashboard template, voice/text actions to :
    - know the status of Recalbox (on/off)
    - know the currently played game
    - try to launch a game (not yet working, for know it can search if the file exists, but there is no API to laucnhe the game, and no SSH implementation done yet)