# Recalbox Home Assistant integration - Changelog

> By Aurélien Tomassini, 2026.


## v0.0.3 - Work in progress...

- New screenshot script : it first tries a UDP screenshot. If failed, then it tries a screenshot via API.  
  Used both for voice/text command, and button pressed.
- Update dashboard card and button icons


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