from os import listdir
import os.path
from os.path import isfile, join
import glob
from xml.dom import minidom
import plistlib
import string

import indigo
import sys
import eps
import devactiondefs

class devactions:

	INDIGO_STATUS = 	["statusRequest|Request Full Status Update|id", "~|~|~", "energyupdate|Request Energy Update|id", "resetEnergyAccumTotal|Request Energy Usage|id"]
	INDIGO_RELAY = 		["turnOn|Turn On|id", "turnOff|Turn Off|id", "toggle|Toggle On/Off|id"]
	INDIGO_DIMMER = 	["setBrightness|Set Brightness|id,int", "brighten|Brighten by %|id,int", "dim|Dim by %", "match|Match Brightness|id,int"]
	INDIGO_IO = 		["setBinaryOutput_1|Turn On Output|id,[binaryOutputsAll],bool=True", "setBinaryOutput_2|Turn Off Output|id,[binaryOutputsAll],bool=False", "setBinaryOutput_3|Turn Off All Outputs|id,[binaryOutputsAll]=*,bool=False"]
	INDIGO_SPRINKLER = 	["run|Run Schedule|id,list", "pause|Pause Schedule|id", "resume|Resume Schedule|id", "stop|Stop (all zones off & clear schedule)|id", "~|~|~", "previousZone|Activate Previous Zone|id", "nextZone|Activate Next Zone|id", "~|~|~", "setActiveZone|Turn On Specific Zone|id,int"]
	
	
	#
	# Initialize the class
	#
	def __init__ (self, parent):
		self.parent = parent
		self.version = "1.0"
		
		self.CACHE = indigo.Dict()
		
		self.cachePluginActions()
		
	#
	# Debug log
	#
	def debugLog (self, value):
		if self.parent is None: return
		self.parent.debugLog (value)
		
	#
	# Read all plugin actions
	#
	def cachePluginActions (self):
		try:
			base = indigo.server.getInstallFolderPath() + "/Plugins"
			plugins = glob.glob(base + "/*.indigoPlugin")
			
			for plugin in plugins:
				pluginInfo = self.parsePlist (plugin)
				p = indigo.Dict()
				p["id"] = pluginInfo[0]
				p["name"] = pluginInfo[1]
				p["actions"] = {}
					
				indigo.server.log("Caching %s (%s)" % (p["name"], p["id"]))
					
				if os.path.isfile(plugin + "/Contents/Server Plugin/Actions.xml"):
					x = minidom.parse(plugin + "/Contents/Server Plugin/Actions.xml")
					actions = x.getElementsByTagName('Action')
					indigo.server.log("\tReading %i actions" % len(actions))
					
					actionIdx = 0
					allactions = indigo.Dict()
					
					for action in actions:
						paction = {}
						
						paction["id"] = action.attributes["id"].value
						paction["name"] = ""
						paction["callback"] = ""
						paction["devicefilter"] = ""
						paction["uipath"] = ""
						paction["separator"] = False
						paction["order"] = actionIdx
						paction["generic"] = True
						
						try:
							paction["devicefilter"] = action.attributes["deviceFilter"].value
						except:
							paction["devicefilter"] = "" # nothing we can do about it
						
						if paction["devicefilter"] != "":
							paction["devicefilter"] = paction["devicefilter"].replace("self", p["id"])
							
						#indigo.server.log(paction["devicefilter"])
							
						try:
							paction["uipath"] = action.attributes["uiPath"].value
						except:
							paction["uipath"] = "" # nothing we can do about it
						
						callback = action.getElementsByTagName("CallbackMethod")
						if callback:
							for c in callback:
								if c.parentNode.localName.lower() != "field":
									paction["callback"] = c.childNodes[0].data
									
						aname = action.getElementsByTagName("Name")
						if aname:
							for a in aname:
								paction["name"] = a.childNodes[0].data
								
						configUI = action.getElementsByTagName("ConfigUI")
						if configUI:
							paction["generic"] = False
								
						#if device != "":
						#	indigo.server.log("\t\tCached action '%s' method %s for action ID %s for '%s' devices" % (name, cb, id, device))
						#else:
						#	indigo.server.log("\t\tCached action '%s' method %s for action ID %s" % (name, cb, id))
						
						
						if action.hasChildNodes() == False:
							# Fields have children, seps do not
							#indigo.server.log("\t\t\tThis is a separator")	
							paction["separator"] = True
						
						allactions[paction["id"]] = paction
						actionIdx = actionIdx + 1
					
					p["actions"] = allactions
							
				self.CACHE[pluginInfo[0]] = p	
				
			#indigo.server.log(unicode(self.CACHE))				
							
		except Exception as e:
			eps.printException(e)
			
	
	#
	# Parse plist line data
	#
	def parsePlist (self, path):
		try:
			plist = open(path + "/Contents/Info.plist")
			nameIdx = 0
			name = ""
			idIdx = 0
			id = ""
			for line in plist:
				if nameIdx == 1:
					name = line
					nameIdx = 0
					continue
					
				if idIdx == 1:
					id = line
					idIdx = 0
					continue
					
				x = string.find (line, 'CFBundleDisplayName')
				if x > -1: nameIdx = 1
				
				x = string.find (line, 'CFBundleIdentifier')
				if x > -1: idIdx = 1
				
			#indigo.server.log (name + "\t" + id)
			
			x = string.find (name, "<string>")
			y = string.find (name, "</string>")
			name = name[x + 8:y]
			
			x = string.find (id, "<string>")
			y = string.find (id, "</string>")
			id = id[x + 8:y]
			
			return [id, name]
		
		except Exception as e:
			eps.printException(e)
			
		return ["Unknown", "Unknown"]
	
	
	#
	# Compose device operations list 1.0.6
	#
	def getIndigoOperations (self, filter, valuesDict=None, typeId="", targetId=0):
		myArray = [("default", "No compatible Indigo or device operations found")]
		filter = str(filter)
	
		try:
			if filter == "": return myArray
		
			retAry = []
		
			l = ""
			for i in range (0, 25):
				l += unicode("\xc4", "cp437")
			
			line = ["-1|" + l]
		
			capable = []
		
			# If we are filtering for the target device get some info about it, otherwise use the filter passed
			if filter[0] == "#":
				if eps.valueValid (valuesDict, filter[1:], True):
					targetId = int(valuesDict[filter[1:]])
					filter = "targetId"
				else:
					filter = "none"
		
			thisFilter = filter.lower()
		
			if filter == "targetId":
				thisFilter = "none"
			
				dev = indigo.devices[int(targetId)]
				#indigo.server.log(unicode(type(dev)))
			
				#indigo.server.log(unicode(dev))
			
				if dev.supportsStatusRequest: capable.append("status")
				if unicode(type(dev)) == "<class 'indigo.DimmerDevice'>": capable.append("dimmer")
				if unicode(type(dev)) == "<class 'indigo.RelayDevice'>": capable.append("relay")
				if unicode(type(dev)) == "<class 'indigo.SprinklerDevice'>": capable.append("sprinkler")
			
			# Relay device commands
			lists = 0
		
			if "status" in capable:
				cmdList = ["fullstatus|Request Full Status Update"]
				retAry = self.appendOptionList (retAry, cmdList)
				retAry = self.appendOptionList (retAry, line)
			
				cmdList = ["energyupdate|Request Energy Update", "energyusage|Request Energy Usage"]
				retAry = self.appendOptionList (retAry, cmdList)
			
				lists = lists + 1
				if len(capable) > lists: retAry = self.appendOptionList (retAry, line)
		
			if "relay" in capable:
				cmdList = devactiondefs.INDIGO_RELAY
				retAry = self.appendOptionList (retAry, cmdList)
				lists = lists + 1
				if len(capable) > lists: retAry = self.appendOptionList (retAry, line)
			
			if "dimmer" in capable:
				cmdList = devactiondefs.INDIGO_DIMMER
				retAry = self.appendOptionList (retAry, cmdList)
				lists = lists + 1
				if len(capable) > lists: retAry = self.appendOptionList (retAry, line)
				
			if "sprinkler" in capable:
				cmdList = devactiondefs.INDIGO_SPRINKLER
				retAry = self.appendOptionList (retAry, cmdList)
				lists = lists + 1
				if len(capable) > lists: retAry = self.appendOptionList (retAry, line)
		
			if dev:	
				if dev.pluginId != "" or dev.deviceTypeId != "":
					# Not a built-in Indigo device						
					actionAry = self.getCachedActions (dev)
				
					if len(actionAry) > 0 and len(capable) > 0: retAry = self.appendOptionList (retAry, line) # Separate the specific commands
				
					for s in actionAry:
						retAry.append (s)
					
			if len(retAry) > 0:
				return retAry
			else:
				return myArray
	
		except:
			return myArray
		
	#
	# Determine a device parent type
	#
	

	#
	# Read a list and append options to the destination list - 1.0.6
	#
	def appendOptionList (self, dstList, srcList):
		l = ""
		for i in range (0, 25):
			l += unicode("\xc4", "cp437")
				
		for s in srcList:
			data = s.split("|")
			
			if data[0] == "~":
				option = ("-1", l)	
			else:
				option = (data[0], data[1])

			dstList.append(option)
		
		return dstList
	
	#
	# Get action list from cache and return
	#
	def getCachedActions (self, dev):
		retAry = []
		
		try:
			# Anything without a type or id is typically an Indigo internal that we handle already
			if dev.pluginId == "" or dev.deviceTypeId == "":
				indigo.server.log("%s seems to be a built-in Indigo device that is not yet supported.\n\nIf you would like to see support for this device in future versions please post a request on the forum.\nPlugin:%s\nType:%s" % (dev.name, dev.pluginId, dev.deviceTypeId), isError=True)
				return retAry
		
			try:
				plugin = self.CACHE[dev.pluginId]
			except:
				indigo.server.log("%s does not have a cache, something may be wrong" % dev.name, isError=True)
				return retAry
				
			l = ""
			for i in range (0, 25):
				l += unicode("\xc4", "cp437")
			
			line = ["-1|" + l]			
				
			
			#indigo.server.log("\n" + unicode(plugin["actions"]))
			
			tempAry = []
			for i in range (0, len(plugin["actions"])):
				tempAry = self.appendOptionList (tempAry, line)
				
			for id, action in plugin["actions"].iteritems():
				isMatch = self.matchesDevice (dev, plugin, action)
				
				for index, item in enumerate(tempAry):
					if action["separator"]: continue # that is already the default value
					
					if action["uipath"] == "hidden": continue
					if isMatch == False: continue
					
					if index == action["order"]: 
						option = (action["callback"], action["name"])
						tempAry[index] = option
						
			#indigo.server.log(unicode(plugin))
			
			# Now audit the list to clean up entries that were not added
			newAry = []
			for index, item in enumerate(tempAry):
				for id, action in plugin["actions"].iteritems():
					if index == action["order"]:
						isMatch = self.matchesDevice (dev, plugin, action)
						
						if isMatch and action["uipath"] != "hidden" and action["generic"]: 
							newAry.append(tempAry[index])
						elif isMatch and action["generic"] == False and self.hasDefinedAction (dev, action["id"]):
							newAry.append(tempAry[index])
							
			# Final audit to clean up anywhere that has strange separators
			if len(newAry) > 1:
				lastItem = None
				for index, item in enumerate(newAry):
					if lastItem is None:
						# Make sure the first item is not a separator
						if newAry[index] == self.appendOptionList ([], line): continue
				
						lastItem = newAry[index]
						continue
					
					if lastItem != newAry[index]:
						retAry.append(newAry[index])
			else:
				retAry = newAry # Only one item, nothing more to do
							
			return retAry
		
		except Exception as e:
			eps.printException(e)
			return []
	
	
	#
	# See if a given action matches the device
	#
	def matchesDevice (self, dev, plugin, action):
		try:
			deviceMatch = False
						
			if action["devicefilter"] == "":			
				deviceMatch = True
				
			elif action["devicefilter"] == plugin["id"]:
				deviceMatch = True
				
			elif action["devicefilter"] == plugin["id"] + "." + dev.deviceTypeId:
				deviceMatch = True
			
			elif action["devicefilter"] != "":
				devFind = string.find (action["devicefilter"], plugin["id"] + "." + dev.deviceTypeId)
				if devFind > -1:
					deviceMatch = True
				else:
					devFind = string.find (action["devicefilter"], plugin["id"])
					if devFind > -1:
						devStr = action["devicefilter"][devFind:]
						
						# In case there is a comma
						devAry = devStr.split(",")
						
						if devAry[0] == plugin["id"]: deviceMatch = True
						if devAry[0] == plugin["id"] + "." + dev.deviceTypeId: deviceMatch = True
						
		
		except Exception as e:
			eps.printException(e)
			
		return deviceMatch
	
	#
	# See if we have a defined action for non-generic actions that require parameters
	#
	def hasDefinedAction (self, dev, actionId):
		try:
			# This is a future feature, we will be checking if this action ID for this device has been defined
			return False
			
		except Exception as e:
			eps.printException(e)
	
	#
	# Return custom action option array for device and action
	#
	def getOptionFields (self, dev, action):
		retVal = []
		cmdList = []
		
		try:
			if unicode(type(dev)) == "<class 'indigo.DimmerDevice'>": cmdList += devactiondefs.INDIGO_DIMMER
			if unicode(type(dev)) == "<class 'indigo.RelayDevice'>": cmdList += devactiondefs.INDIGO_RELAY
			if unicode(type(dev)) == "<class 'indigo.SprinklerDevice'>": cmdList += devactiondefs.INDIGO_SPRINKLER
		
			for s in cmdList:
				cmds = s.split("|")
				if cmds[0] == action:
					opts = cmds[2].split(",")
					for opt in opts:
						indigo.server.log(opt)
						x = string.find (opt, "=")
						if x > -1:
							o = opt.split("=")
							indigo.server.log(unicode(o))
							retVal.append(o[1])
						
					indigo.server.log(unicode(cmds))
		
		except Exception as e:
			eps.printException(e)
			
		indigo.server.log(unicode(retVal))
			
		return retVal
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	