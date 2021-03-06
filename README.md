Scene Toggle
==========

A plugin for the Indigo home automation system (http://indigodomo.com)

Scene Toggle is just as the name implies, lets you toggle on and off a scene.  While this functionality exists in Indigo already by using virtual devices this plugin takes it a step further.

The scene device lets you choose which On/Off or Dimmable devices in your network that you want included in the scene.  You set the devices to be off, on or the brightness you desire and the device takes a "snapshot" of the devices for the scene.

For more information and documentation please visit http://forums.indigodomo.com/viewtopic.php?f=194&t=16118

Scene Toggle on Indigo 6
-------------------
If you are using Indigo 6 then you will need to install Scene Toggle version 1.0, that is the last Indigo 6 stable release.  No further development, short of major bug squashing, will be done for any version prior to 2.0.

About This Repo
-------------------

This repo is only for Indigo 7 while it is still in BETA, once Indigo 7 drops this repo will merged into the main Scene Toggle repo.  Access to this repo is private and restricted only to participants in the Indigo 7 BETA, please do not distribute this copy to anyone not participating in the BETA testing.

Known Issues / Wish List
-------------------
* Add new device or modify existing to support dynamic sunrise/sunset dimming (see post in forum for Alarm Clock for user suggestion)
* Redesign device UI

Beta Release Notes
-------------------
<<<<<<< HEAD
July 13, 2016: Beta 1a
* Moved all device-specific commands to the Indigo device actions menu, left "clear all devices" in the top level menu
* Added separators to actions to clean it up
* Added standard PluginConfig.xml file
* Changed Menuitems.xml to conform to standards
* Re-titled all device actions now made redundant by converting to relay like on/off/toggle
* Moved plugin to standard EPS architecture file
* Removed redundant (and now invalid) onOffState

* Added upgrade for previous versions to convert the previous "custom" device into a relay device for compatibility with other EPS plugins
=======
July 13, 2016: PENDING
* Beta development on this release for I7 is pending
>>>>>>> origin/master
