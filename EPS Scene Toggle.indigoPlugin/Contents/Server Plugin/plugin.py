#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################

import indigo

import os
import sys
import time
import datetime

################################################################################
class Plugin(indigo.PluginBase):
	#
	# Init
	#
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.debug = False
		
	def __del__(self):
		indigo.PluginBase.__del__(self)
		
	#
	# Snapshot button pressed in configuration
	#
	def snapshotDeviceList (self, valuesDict, typeId, devId):
		dev = indigo.devices[devId]
		props = self.snapShot (valuesDict["toggledevices"], dev, "snapshot")
		
		# Since we are doing this inside the config, write the new values
		valuesDict["snapshot"] = props
		return valuesDict
		
	#
	# Clear actions button pressed in configuration
	#
	def clearActionList (self, valuesDict, typeId, devId):
		valuesDict["onBeforeTurnedOn"] = ""
		valuesDict["onBeforeTurnedOff"] = ""
		valuesDict["onAfterTurnedOn"] = ""
		valuesDict["onAfterTurnedOff"] = ""
		
		return valuesDict
		
	#
	# Snapshot for the saved scene or pre-scene settings
	#
	def snapShot (self, deviceList, dev, snaptype):
		# Read the snapshot from the plugin and clear the it
		props = dev.pluginProps
		newsnapshot = []
					
		# Run through all devices and save their current state
		for d in deviceList:
			thisdev = indigo.devices[int(d)]
			passes = False
			
			snapshot = str(thisdev.id) + "|" + thisdev.name + "|"
			
			if "brightnessLevel" in thisdev.states:
				if snaptype == "snapshot":
					snapshot = snapshot + str(thisdev.states["brightnessLevel"]) + "|"
				else:			
					if dev.ownerProps["turnoff"]:
						snapshot = snapshot + "0|"
					else:
						snapshot = snapshot + str(thisdev.states["brightnessLevel"]) + "|"
					
				passes = True
			else:
				snapshot = snapshot + "0|"
				
			if "onOffState" in thisdev.states:
				if snaptype == "snapshot":
					if thisdev.states["onOffState"]:
						snapshot = snapshot + "on"
					else:
						snapshot = snapshot + "off"
				else:
					if dev.ownerProps["turnoff"]:
						snapshot = snapshot + "off"
					else:
						if thisdev.states["onOffState"]:
							snapshot = snapshot + "on"
						else:
							snapshot = snapshot + "off"
						
				passes = True
			else:
				snapshot = snapshot + "off"
			
			if passes == False:
				indigo.server.log(thisdev.name + " cannot be managed through the scene named " + dev.name + " because it doesn't support On/Off or brightness")
			else:			
				newsnapshot.append(snapshot)
			
		#props[snaptype] = ["device1", "device2"]
		props[snaptype] = newsnapshot
		
		dev.replacePluginPropsOnServer(props)
		
		return props[snaptype] # only return the snapshotted data for in-config snapshots
		
		
	#
	# Save snapshot action
	#
	def saveSnapshot (self, devAction):
		dev = indigo.devices[devAction.deviceId]
		self.snapShot (dev.ownerProps["toggledevices"], dev, "snapshot")
		indigo.server.log("Snapshot saved for " + dev.name)
		
	#
	# Run scene action
	#
	def sceneAction (self, devAction):
		dev = indigo.devices[devAction.deviceId]
		
		if devAction.pluginTypeId == "turnOn":
			self.activateScene (dev, "snapshot")
		elif devAction.pluginTypeId == "turnOff":
			self.activateScene (dev, "memory")
		elif devAction.pluginTypeId == "toggle":
			if dev.states["onOffState"]:
				self.debugLog(u"Turning off " + dev.name)
				self.activateScene (dev, "memory")
			else:
				self.debugLog(u"Turning on " + dev.name)
				self.activateScene (dev, "snapshot")
		elif devAction.pluginTypeId == "propertyDump":
			indigo.server.log (unicode(dev))
		elif devAction.pluginTypeId == "clearMemory":
			self.clearMemory (dev)
			indigo.server.log ("Cleared " + dev.name + " pre-scene memory")
		elif devAction.pluginTypeId == "testing":
			self.processTimer()
			
	#
	# Clear pre-scene memory
	#
	def clearMemory (self, dev):
		props = dev.pluginProps
		props["memory"] = []
		dev.replacePluginPropsOnServer(props)
	
	#
	# Activate a scene
	#
	def activateScene (self, dev, snaptype):
		# Set the memory for this scene
		if snaptype == "snapshot":
			if dev.ownerProps["onBeforeTurnedOn"] != "":
				indigo.actionGroup.execute(int(dev.ownerProps["onBeforeTurnedOn"]))
				
			self.snapShot (dev.ownerProps["toggledevices"], dev, "memory")
		else:
			if dev.ownerProps["onBeforeTurnedOff"] != "":
				indigo.actionGroup.execute(int(dev.ownerProps["onBeforeTurnedOff"]))
				
			if dev.ownerProps["liveupdate"] == True:
				# We are turning off the scene and they want to snapshot the current settings
				self.snapShot (dev.ownerProps["toggledevices"], dev, "snapshot")
		
		# Read the snapshot for this scene and execute actions
		for snapshot in dev.pluginProps[snaptype]:
			details = snapshot.split("|")
			d = indigo.devices[int(details[0])]
			
			if "brightnessLevel" in d.states:
				target = d.states["brightnessLevel"] - int(details[2])
				
				if target == d.states["brightnessLevel"]:
					# Means the setting was zero, or off, turn device off
					if d.states["onOffState"]:
						self.debugLog(u"Turning off " + d.name)
						indigo.device.turnOff (d.id)
					
				elif target > 0:
					if d.states["brightnessLevel"] != target:
						self.debugLog(u"Dimming " + d.name + " to " + str(target))
						indigo.dimmer.dim (d.id, by=target)
				elif target < 0:
					target = target * -1
					
					if d.states["brightnessLevel"] != target:
						self.debugLog(u"Brightening " + d.name + " to " + str(target))
						indigo.dimmer.brighten (d.id, by=target)
			else:
				# Since we already validated the devices we can just do on/off
				if details[3] == "off":
					if d.states["onOffState"]:
						self.debugLog(u"Turning off " + d.name)
						indigo.device.turnOff (d.id)
				else:
					if d.states["onOffState"] == False:
						self.debugLog(u"Turning on " + d.name)
						indigo.device.turnOn (d.id)
					
		# Make sure there were no errors changing the states of the devices, if so then re-run
		
		# Change our state
		if snaptype == "snapshot":
			dev.updateStateOnServer("onOffState", True)	
			dev.updateStateOnServer("lastOnTime", str(datetime.datetime.now()))	
			
			# If they set a timer for the scene, implement the schedule to turn it off now
			if dev.ownerProps["timeout"] != "0":
				indigo.server.log ("Turning off automatically")
				dev.updateStateOnServer("timeRemaining", str(dev.ownerProps["timeout"]))
				
			# Perform after turned on action
			if dev.ownerProps["onAfterTurnedOn"] != "":
				indigo.actionGroup.execute(int(dev.ownerProps["onAfterTurnedOn"]))
				
		else:
			dev.updateStateOnServer("onOffState", False)
			
			# Perform after turned off action
			if dev.ownerProps["onAfterTurnedOff"] != "":
				indigo.actionGroup.execute(int(dev.ownerProps["onAfterTurnedOff"]))
				
		# If not activating the snapshot then we are activating memory, once activated clear it out
		if snaptype != "snapshot":
			self.clearMemory (dev)
			
	#
	# Recalculate remaining time and shut off if zero
	#
	def processTimer (self):
		#indigo.server.log ("Process timer")
		for dev in indigo.devices:
			if dev.pluginId == "com.eps.indigoplugin.scene-toggle":
				if dev.states["timeRemaining"] != 0:
					#indigo.server.log ("Has time remaining")
					curtime = datetime.datetime.now()
					laston = datetime.datetime.strptime(dev.states["lastOnTime"], "%Y-%m-%d %I:%M:%S.%f")
					
					elapsed = curtime - laston
					minutes = elapsed.seconds / 60
					
					if minutes >= int(dev.ownerProps["timeout"]):
						# Time has elapsed, turn off the scene
						minutes = 0
						dev.updateStateOnServer("timeRemaining", 0)
						self.snapShot (dev.ownerProps["toggledevices"], dev, "snapshot")
						
					else:
						dev.updateStateOnServer("timeRemaining", str(minutes))
						
		
	#
	# Device configuration dialog closing
	#
	def validateDeviceConfigUi (self, valuesDict, typeId, devId):
		errorDict = indigo.Dict()
		
		# Make sure if they turned off action groups to clear them out
		if valuesDict["actions"] == False :
			valuesDict["onBeforeTurnedOn"] = ""
			valuesDict["onBeforeTurnedOff"] = ""
			valuesDict["onAfterTurnedOn"] = ""
			valuesDict["onAfterTurnedOff"] = ""
		
			return (True, valuesDict, errorDict)	
			
		return True
		
	#
	# Plugin device start
	#	
	def deviceStartComm (self, dev):
		self.debugLog(u"device start comm called")
		dev.stateListOrDisplayStateIdChanged() # Force plugin to refresh states from devices.xml
		
		if dev.id == 1469682740:
			dev = indigo.device.changeDeviceTypeId(dev, "epsst")

	#
	# Relay actions
	#
	def actionControlDimmerRelay(self, action, dev):
	
		if action.deviceAction == indigo.kDimmerRelayAction.TurnOn:
			# Command hardware module (dev) to turn ON here:
			# ** IMPLEMENT ME **
			self.activateScene (dev, "snapshot")
			sendSuccess = True		# Set to False if it failed.

			if sendSuccess:
				# If success then log that the command was successfully sent.
				indigo.server.log(u"sent \"%s\" %s" % (dev.name, "on"))

				# And then tell the Indigo Server to update the state.
				dev.updateStateOnServer("onOffState", True)
			else:
				# Else log failure but do NOT update state on Indigo Server.
				indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "on"), isError=True)
				
		###### TURN OFF ######
		elif action.deviceAction == indigo.kDimmerRelayAction.TurnOff:
			# Command hardware module (dev) to turn OFF here:
			# ** IMPLEMENT ME **
			self.activateScene (dev, "memory")
			sendSuccess = True		# Set to False if it failed.

			if sendSuccess:
				# If success then log that the command was successfully sent.
				indigo.server.log(u"sent \"%s\" %s" % (dev.name, "off"))

				# And then tell the Indigo Server to update the state:
				dev.updateStateOnServer("onOffState", False)
			else:
				# Else log failure but do NOT update state on Indigo Server.
				indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "off"), isError=True)

		###### TOGGLE ######
		elif action.deviceAction == indigo.kDimmerRelayAction.Toggle:
			# Command hardware module (dev) to toggle here:
			# ** IMPLEMENT ME **
			newOnState = not dev.onState
			sendSuccess = True		# Set to False if it failed.

			if sendSuccess:
				# If success then log that the command was successfully sent.
				indigo.server.log(u"sent \"%s\" %s" % (dev.name, "toggle"))

				# And then tell the Indigo Server to update the state:
				dev.updateStateOnServer("onOffState", newOnState)
			else:
				# Else log failure but do NOT update state on Indigo Server.
				indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "toggle"), isError=True)

	#
	# Plugin startup
	#
	def startup(self):
		self.debugLog(u"startup called")
	
	#	
	# Plugin shutdown
	#
	def shutdown(self):
		self.debugLog(u"shutdown called")

	#
	# Concurrent Threading
	#
	def runConcurrentThread(self):
		try:
			while True:
					#self.processTimer()
					self.sleep(1)
		except self.StopThread:
			pass	

	
