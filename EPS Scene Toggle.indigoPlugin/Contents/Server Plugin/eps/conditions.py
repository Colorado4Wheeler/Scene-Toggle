import datetime
import time
import indigo
import sys
import dtutil
import eps
import string
import ui
import calendar

class conditions:

	#
	# Initialize the class
	#
	def __init__ (self, parent):
		self.parent = parent
		self.maxConditions = 10
		self.enablePlaceholders = True 
		
		self.version = "2.2"
		
	#
	# Debug log
	#
	def debugLog (self, value):
		if self.parent is None: return
		self.parent.debugLog (value)	
		
	################################################################################
	# CONDITION CHECKING
	################################################################################
		
	#
	# Check if conditions pass, return false on any condition failure
	#
	def conditionsPass (self, propsDict):
		try:
			isTrue = 0
			isFalse = 0
			
			if eps.valueValid (propsDict, "conditions", True) == False: return False
			condition = propsDict["conditions"]
			
			self.parent.logger.debug ("\tCondition is set to %s, testing condition(s)" % condition)
			
			if condition == "none": return True
			
			for i in range (0, self.maxConditions + 1):
				if eps.valueValid (propsDict, "condition" + str(i), True) == False: continue # no condition for this index
				if propsDict["condition" + str(i)] == "disabled": continue # this condition is disabled
				
				val = [0,0] # Failsafe
				
				if propsDict["evaluation" + str(i)] == "between" or propsDict["evaluation" + str(i)] == "notbetween": val = self.conditionBetween (propsDict, i)
				if propsDict["evaluation" + str(i)] == "equal" or propsDict["evaluation" + str(i)] == "notequal": val = self.conditionEquals (propsDict, i)
				if propsDict["evaluation" + str(i)] == "greater": val = self.conditionGreater (propsDict, i)
				if propsDict["evaluation" + str(i)] == "less": val = self.conditionLess (propsDict, i)
				if propsDict["evaluation" + str(i)] == "contains" or propsDict["evaluation" + str(i)] == "notcontains": val = self.conditionContain (propsDict, i)
				if propsDict["evaluation" + str(i)] == "in" or propsDict["evaluation" + str(i)] == "notin": val = self.conditionIn (propsDict, i) # 2.2
					
				isTrue = isTrue + val[0]
				isFalse = isFalse + val[1]			
		
			self.parent.logger.debug("\tConditions returning true: %i, returning false: %i" % (isTrue, isFalse))
		
			if condition == "alltrue" and isFalse <> 0: 
				self.parent.logger.debug("\tCondition checking is for All True and there is a false value")
				return False
			if condition == "anytrue" and isTrue == 0: 
				self.parent.logger.debug("\tCondition checking is for Any True and there are no true values")
				return False
			if condition == "allfalse" and isTrue <> 0: 
				self.parent.logger.debug("\tCondition checking is for All False and there is a true value")
				return False
			if condition == "anyfalse" and isFalse == 0: 
				self.parent.logger.debug("\tCondition checking is for Any False and there are no false values")
				return False
			
			return True
		
		except Exception as e:
			eps.printException(e) 
			return False
	
	
	#
	# Check condition evaluation IN
	#
	def conditionIn (self, propsDict, index):
		ret = []
		isTrue = 0
		isFalse = 0
		
		try:
			compareString = ""
			devEx = None
			
			if propsDict["condition" + str(index)] == "device" or propsDict["condition" + str(index)] == "devstatedateonly" or propsDict["condition" + str(index)] == "devstatetimeonly" or propsDict["condition" + str(index)] == "devstatedatetime" or propsDict["condition" + str(index)] == "devstatedow":
				devEx = indigo.devices[int(propsDict["device" + str(index)])]
			
			if propsDict["condition" + str(index)] == "device":
				if eps.valueValid (devEx.states, propsDict["state" + str(index)]):
					compareString = unicode(devEx.states[propsDict["state" + str(index)]])
			
			elif propsDict["condition" + str(index)] == "variable":
				var = indigo.variables[int(propsDict["variable" + str(index)])]
				compareString = unicode(var.value)
				
			elif propsDict["condition" + str(index)] == "datetime" or propsDict["condition" + str(index)] == "devstatedatetime" or propsDict["condition" + str(index)] == "vardatetime":			
				d = indigo.server.getTime()
				if propsDict["condition" + str(index)] == "devstatedatetime": d = self.getDevStateDateTime (propsDict, devEx, index)
				if propsDict["condition" + str(index)] == "vardatetime": d = self.getVarDateTime (propsDict, index)
				
				# Get the comparison
				startDate = self.getDateComparison (propsDict, index, d, "start")
				
				#compareString = d.strftime ("%Y-%m-%d %H:%M:%S | %m %b %B | %A %w | %I | %p")
				compareString = ""
				
				# Build a compare string based on the date/time options
				if propsDict["startDow" + str(index)] != "any":	
					if compareString == "":
						compareString += startDate.strftime("%A")
					else:
						compareString += startDate.strftime(" %A")
						
				if propsDict["startMonth" + str(index)] != "any": 
					if compareString == "":
						compareString += startDate.strftime("%B")
					else:
						compareString += startDate.strftime(" %B")
						
				if propsDict["startDay" + str(index)] != "any":	
					if compareString == "":
						compareString += startDate.strftime("%d")
					else:
						compareString += startDate.strftime(" %-d")
						
				if propsDict["startYear" + str(index)] != "any": 
					if compareString == "":
						compareString += startDate.strftime("%Y")
					else:
						compareString += startDate.strftime(" %Y")
						
				if propsDict["startTime" + str(index)] != "any": 
					if compareString == "":
						compareString += startDate.strftime("%H:%M %p")
					else:
						compareString += startDate.strftime(" %H:%M %p")
				
			else:
				self.parent.logger.error("Unknown condition %s in contains" % propsDict["condition" + str(index)])
				
			self.parent.logger.debug ("\tChecking if %s is in %s" % (compareString, propsDict["value" + str(index)]))
			
			compareValue = ""
			if compareString != "": compareValue = compareString.lower()
			
			findValue = ""
			if propsDict["value" + str(index)] != "": findValue = str(propsDict["value" + str(index)]).lower()
			
			if findValue != "":
				foundAt = string.find (findValue.lower(), compareString.lower())
				self.parent.logger.threaddebug("Looking for %s in %s resulted in an index of %i" % (compareValue, findValue, foundAt))
			
				if foundAt > -1:
					isTrue = 1	
				else:
					# It's the negative version so reverse the values
					isFalse = 1
			
			else:
				if compareValue == "":
					isTrue = 1
				else:
					isFalse = 1
					
		except Exception as e:
			eps.printException(e) 
			isTrue = 0
			isFalse = 0
			
		ret.append(isTrue)
		ret.append(isFalse)
		
		return ret
	
	#
	# Check condition evaluation CONTAINS
	#
	def conditionContain (self, propsDict, index):
		ret = []
		isTrue = 0
		isFalse = 0
		
		try:
			compareString = ""
			devEx = None
			
			if propsDict["condition" + str(index)] == "device" or propsDict["condition" + str(index)] == "devstatedateonly" or propsDict["condition" + str(index)] == "devstatetimeonly" or propsDict["condition" + str(index)] == "devstatedatetime" or propsDict["condition" + str(index)] == "devstatedow":
				devEx = indigo.devices[int(propsDict["device" + str(index)])]
			
			if propsDict["condition" + str(index)] == "device":
				if eps.valueValid (devEx.states, propsDict["state" + str(index)]):
					compareString = unicode(devEx.states[propsDict["state" + str(index)]])
			
			elif propsDict["condition" + str(index)] == "variable":
				var = indigo.variables[int(propsDict["variable" + str(index)])]
				compareString = unicode(var.value)
				
			elif propsDict["condition" + str(index)] == "datetime" or propsDict["condition" + str(index)] == "devstatedatetime" or propsDict["condition" + str(index)] == "vardatetime":
				d = indigo.server.getTime()
				if propsDict["condition" + str(index)] == "devstatedatetime": d = self.getDevStateDateTime (propsDict, devEx, index)
				if propsDict["condition" + str(index)] == "vardatetime": d = self.getVarDateTime (propsDict, index)
				
				compareString = d.strftime ("%Y-%m-%d %H:%M:%S | %m %b %B | %A %w | %I | %p")
				
			else:
				self.parent.logger.error("Unknown condition %s in contains" % propsDict["condition" + str(index)])
				
			self.parent.logger.debug ("\tChecking if %s is in %s" % (propsDict["value" + str(index)], compareString))
			
			compareValue = ""
			if compareString != "": compareValue = compareString.lower()
			
			findValue = ""
			if propsDict["value" + str(index)] != "": findValue = str(propsDict["value" + str(index)]).lower()
			
			if findValue != "":
				foundAt = string.find (compareString, findValue)
				self.parent.logger.threaddebug("Looking for %s in %s resulted in an index of %i" % (findValue, compareValue, foundAt))
				
				if foundAt > -1:
					isTrue = 1	
				else:
					# It's the negative version so reverse the values
					isFalse = 1
			
			else:
				if compareValue == "":
					isTrue = 1
				else:
					isFalse = 1
		
		except Exception as e:
			eps.printException(e) 
			isTrue = 0
			isFalse = 0
			
		ret.append(isTrue)
		ret.append(isFalse)
		
		return ret
		
	
	#
	# Check condition evaluation LESS THAN
	#
	def conditionLess (self, propsDict, index):
		ret = []
		isTrue = 0
		isFalse = 0
		
		try:
			if propsDict["condition" + str(index)] == "datetime" or propsDict["condition" + str(index)] == "devstatedatetime" or propsDict["condition" + str(index)] == "vardatetime": val = self.conditionsDate (propsDict, index)
			
			if propsDict["condition" + str(index)] == "device":
				val = [0, 0] # Failsafe
				devEx = indigo.devices[int(propsDict["device" + str(index)])]
				if eps.valueValid (devEx.states, propsDict["state" + str(index)]):
					compareString = unicode(devEx.states[propsDict["state" + str(index)]])
					self.parent.logger.debug ("\tChecking if device state '%s' value of '%s' is less than '%s'" % (propsDict["state" + str(index)], compareString, propsDict["value" + str(index)]))
					
					if compareString.lower() < propsDict["value" + str(index)].lower():
						val[0] = 1
						val[1] = 0
					else:
						val[0] = 0
						val[1] = 1
						
			if propsDict["condition" + str(index)] == "variable":
				val = [0, 0] # Failsafe
				var = indigo.variables[int(propsDict["variable" + str(index)])]
				compareString = unicode(var.value)
				self.parent.logger.debug ("\tChecking if variable '%s' value of '%s' is less than '%s'" % (var.name, compareString, propsDict["value" + str(index)]))
									
				if compareString.lower() < propsDict["value" + str(index)].lower():
					val[0] = 1
					val[1] = 0
				else:
					val[0] = 0
					val[1] = 1
		
			isTrue = isTrue + val[0]
			isFalse = isFalse + val[1]			
		
		except Exception as e:
			eps.printException(e) 
			isTrue = 0
			isFalse = 0
			
		ret.append(isTrue)
		ret.append(isFalse)
		
		return ret
	
	#
	# Check condition evaluation GREATER THAN
	#
	def conditionGreater (self, propsDict, index):
		ret = []
		isTrue = 0
		isFalse = 0
		
		try:
			if propsDict["condition" + str(index)] == "datetime" or propsDict["condition" + str(index)] == "devstatedatetime" or propsDict["condition" + str(index)] == "vardatetime": val = self.conditionsDate (propsDict, index)
			
			if propsDict["condition" + str(index)] == "device":
				val = [0, 0] # Failsafe
				devEx = indigo.devices[int(propsDict["device" + str(index)])]
				if eps.valueValid (devEx.states, propsDict["state" + str(index)]):
					compareString = unicode(devEx.states[propsDict["state" + str(index)]])
					self.parent.logger.debug ("\tChecking if device state '%s' value of '%s' is greater than '%s'" % (propsDict["state" + str(index)], compareString, propsDict["value" + str(index)]))
					
					if compareString.lower() > propsDict["value" + str(index)].lower():
						val[0] = 1
						val[1] = 0
					else:
						val[0] = 0
						val[1] = 1
						
			if propsDict["condition" + str(index)] == "variable":
				val = [0, 0] # Failsafe
				var = indigo.variables[int(propsDict["variable" + str(index)])]
				compareString = unicode(var.value)
				self.parent.logger.debug ("\tChecking if variable '%s' value of '%s' is greater than '%s'" % (var.name, compareString, propsDict["value" + str(index)]))
									
				if compareString.lower() > propsDict["value" + str(index)].lower():
					val[0] = 1
					val[1] = 0
				else:
					val[0] = 0
					val[1] = 1
		
			isTrue = isTrue + val[0]
			isFalse = isFalse + val[1]			
		
		except Exception as e:
			eps.printException(e) 
			isTrue = 0
			isFalse = 0
			
		ret.append(isTrue)
		ret.append(isFalse)
		
		return ret
	
	#
	# Check condition evaluation EQUAL
	#
	def conditionEquals (self, propsDict, index):
		ret = []
		isTrue = 0
		isFalse = 0
		
		try:
			if propsDict["condition" + str(index)] == "datetime" or propsDict["condition" + str(index)] == "devstatedatetime" or propsDict["condition" + str(index)] == "vardatetime": val = self.conditionsDate (propsDict, index)
			
			if propsDict["condition" + str(index)] == "device":
				val = [0, 0] # Failsafe
				devEx = indigo.devices[int(propsDict["device" + str(index)])]
				if eps.valueValid (devEx.states, propsDict["state" + str(index)]):
					compareString = unicode(devEx.states[propsDict["state" + str(index)]])
					self.parent.logger.debug ("\tChecking if device state '%s' value of '%s' is equal to '%s'" % (propsDict["state" + str(index)], compareString, propsDict["value" + str(index)]))
					
					if compareString.lower() == propsDict["value" + str(index)].lower():
						val[0] = 1
						val[1] = 0
					else:
						val[0] = 0
						val[1] = 1
						
			if propsDict["condition" + str(index)] == "variable":
				val = [0, 0] # Failsafe
				var = indigo.variables[int(propsDict["variable" + str(index)])]
				compareString = unicode(var.value)
				self.parent.logger.debug ("\tChecking if variable '%s' value of '%s' is equal to '%s'" % (var.name, compareString, propsDict["value" + str(index)]))
									
				if compareString.lower() == propsDict["value" + str(index)].lower():
					val[0] = 1
					val[1] = 0
				else:
					val[0] = 0
					val[1] = 1
			
			if propsDict["evaluation" + str(index)] == "equal":
				isTrue = isTrue + val[0]
				isFalse = isFalse + val[1]						
			else:
				# It's the negative version so reverse the values
				self.parent.logger.debug ("\tThe value is true and the condition is searching for the opposite, marking result as false: %s" % unicode(val))
				isTrue = isTrue + val[1]
				isFalse = isFalse + val[0]
		
		except Exception as e:
			eps.printException(e) 
			isTrue = 0
			isFalse = 0
			
		ret.append(isTrue)
		ret.append(isFalse)
		
		return ret
		
	#
	# Check condition evaluation BETWEEN
	#
	def conditionBetween (self, propsDict, index):
		ret = []
		isTrue = 0
		isFalse = 0
		
		try:
			if propsDict["condition" + str(index)] == "datetime" or propsDict["condition" + str(index)] == "devstatedatetime" or propsDict["condition" + str(index)] == "vardatetime": val = self.conditionsDate (propsDict, index)
			
			if propsDict["condition" + str(index)] == "device":
				val = [0, 0] # Failsafe
				devEx = indigo.devices[int(propsDict["device" + str(index)])]
				if eps.valueValid (devEx.states, propsDict["state" + str(index)]):
					compareString = unicode(devEx.states[propsDict["state" + str(index)]])
					self.parent.logger.debug ("\tChecking if device state '%s' value of '%s' is between '%s' and '%s'" % (propsDict["state" + str(index)], compareString, propsDict["value" + str(index)], propsDict["endValue" + str(index)]))
					
					if compareString.lower() >= propsDict["value" + str(index)].lower() and compareString.lower() <= propsDict["endValue" + str(index)].lower():
						val[0] = 1
						val[1] = 0
					else:
						val[0] = 0
						val[1] = 1
						
			if propsDict["condition" + str(index)] == "variable":
				val = [0, 0] # Failsafe
				var = indigo.variables[int(propsDict["variable" + str(index)])]
				compareString = unicode(var.value)
				self.parent.logger.debug ("\tChecking if variable '%s' value of '%s' is between '%s' and '%s'" % (var.name, compareString, propsDict["value" + str(index)], propsDict["endValue" + str(index)]))
									
				if compareString.lower() >= propsDict["value" + str(index)].lower() and compareString.lower() <= propsDict["endValue" + str(index)].lower():
					val[0] = 1
					val[1] = 0
				else:
					val[0] = 0
					val[1] = 1
		
			if propsDict["evaluation" + str(index)] == "between":
				isTrue = isTrue + val[0]
				isFalse = isFalse + val[1]						
			else:
				# It's the negative version so reverse the values
				isTrue = isTrue + val[1]
				isFalse = isFalse + val[0]
		
		except Exception as e:
			eps.printException(e) 
			isTrue = 0
			isFalse = 0
			
		ret.append(isTrue)
		ret.append(isFalse)
		
		return ret
	
	
	################################################################################
	# DATE CONDITIONS
	################################################################################	
	
	#
	# Evaluate conditions for date/time
	#
	def conditionsDate (self, propsDict, index):
		ret = []
		isTrue = 0
		isFalse = 0
		
		try:
			d = indigo.server.getTime()
			
			# Since we don't evaluate seconds, we have to convert d to a 0 second date/time
			dx = d.strftime("%Y-%m-%d %H:%M:00")
			d = datetime.datetime.strptime (dx, "%Y-%m-%d %H:%M:%S")
			
			# If we are using a device state date (has devstate as prefix) then use that date instead
			if string.find (propsDict["condition" + str(index)], 'devstate') > -1:
				devEx = indigo.devices[int(propsDict["device" + str(index)])]
				d = self.getDevStateDateTime (propsDict, devEx, index)
				
			# If using a variable
			if string.find (propsDict["condition" + str(index)], 'var') > -1:
				d = self.getVarDateTime (propsDict, index)
				
			# Get the comparison
			startDate = self.getDateComparison (propsDict, index, d, "start")
				
			if propsDict["evaluation" + str(index)] == "equal" or propsDict["evaluation" + str(index)] == "notequal":
				self.parent.logger.debug ("\tChecking if calculated date of %s is equal to comparison date %s" % (startDate.strftime ("%Y-%m-%d %H:%M"), d.strftime ("%Y-%m-%d %H:%M")))
				
				if startDate == d:
					isTrue = 1
				else:
					isFalse = 1
					
			if propsDict["evaluation" + str(index)] == "greater":
				self.parent.logger.debug ("\tChecking if calculated date of %s is greater than comparison date %s" % (startDate.strftime ("%Y-%m-%d %H:%M"), d.strftime ("%Y-%m-%d %H:%M")))
				
				if startDate > d:
					isTrue = 1
				else:
					isFalse = 1
					
			if propsDict["evaluation" + str(index)] == "less":
				self.parent.logger.debug ("\tChecking if calculated date of %s is less than comparison date %s" % (startDate.strftime ("%Y-%m-%d %H:%M"), d.strftime ("%Y-%m-%d %H:%M")))
				
				if startDate < d:
					isTrue = 1
				else:
					isFalse = 1
					
			if propsDict["evaluation" + str(index)] == "between" or propsDict["evaluation" + str(index)] == "notbetween":
				endDate = self.getDateComparison (propsDict, index, d, "end")
				self.parent.logger.debug ("\tChecking if comparison date of %s is between calculated dates of %s to %s" % (d.strftime ("%Y-%m-%d %H:%M"), startDate.strftime ("%Y-%m-%d %H:%M"), endDate.strftime ("%Y-%m-%d %H:%M")))
				
				if d >= startDate and d <= endDate:
					isTrue = 1
				else:
					isFalse = 1
			
		
		except Exception as e:
			eps.printException(e) 
			isTrue = 0
			isFalse = 1
			
		ret.append(isTrue)
		ret.append(isFalse)
		
		return ret
		
	#
	# Get week day iteration for a given month and year
	#
	def getDayIteration (self, year, month, iteration, dow):
		try:
			days = calendar.monthrange(year, month)
			maxDays = days[1]
			
			dow = int(dow)
			iteration = iteration.lower()
			count = 0
			dayidx = 0
			
			for i in range (1, maxDays + 1):
				s = str(year) + "-" + "%02d" % month + "-" + "%02d" % i
				d = datetime.datetime.strptime (s, "%Y-%m-%d")
				
				if int(d.strftime("%w")) == dow:
					count = count + 1
					dayidx = i # the last day that matches our dow
					
					if iteration == "first" and count == 1: return d
					if iteration == "second" and count == 2: return d
					if iteration == "third" and count == 3: return d
					if iteration == "fourth" and count == 4: return d
					
			# If we haven't yet returned then check if it's the last
			if iteration == "last" and count > 0:
				s = str(year) + "-" + "%02d" % month + "-" + "%02d" % dayidx
				d = datetime.datetime.strptime (s, "%Y-%m-%d")
				return d
		
		except Exception as e:
			eps.printException(e) 
	
	
	#
	# Evaluate conditional date against passed date and create a date to compare to
	#
	def getDateComparison (self, propsDict, index, d, prefix):
		curDate = indigo.server.getTime()
		
		try:
			# For now assume all values are equal to the date passed, this allows for use of "any" as
			# the value, because it's "any" that means that field will always match the comparison date
			year = int(d.strftime("%Y"))
			month = int(d.strftime("%m"))
			day = int(d.strftime("%d"))
			hour = int(d.strftime("%H"))
			minute = int(d.strftime("%M"))
			second = 0 # we never care about seconds
			
			# Evaluate the year
			if propsDict[prefix + "Year" + str(index)] == "any": 
				year = year # do nothing, the default is already this
				
			elif propsDict[prefix + "Year" + str(index)] == "current": 
				year = int(curDate.strftime("%Y"))
				
			elif propsDict[prefix + "Year" + str(index)] == "last": 
				year = int(curDate.strftime("%Y")) - 1
				
			elif propsDict[prefix + "Year" + str(index)] == "last": 
				year = int(curDate.strftime("%Y")) + 1	
			
			else:
				year = int(propsDict[prefix + "Year" + str(index)]) # with no other options, they chose an actual year
				
			
			# Evaluate the month - 2.0
			if propsDict[prefix + "Month" + str(index)] == "any": 
				month = month # the default
				
			elif propsDict[prefix + "Month" + str(index)] == "this":
				month = int(curDate.strftime("%m"))
				
			elif propsDict[prefix + "Month" + str(index)] == "last":
				year = int(curDate.strftime("%Y"))
				month = int(curDate.strftime("%m"))
				day = int(curDate.strftime("%d"))
				
				month = month - 1
				if month < 1:
					year = year - 1
					month = 12
				
				# Check that the new date allows for todays day number
				dayx = calendar.monthrange(year, month)
				if dayx[1] < day: day = dayx[1]
				
			else:
				month = int(propsDict[prefix + "Month" + str(index)]) # they chose the month
			
			# Evaluate the day
			if propsDict[prefix + "Day" + str(index)] == "any":
				day = day # do nothing, the default is already this
				
			elif propsDict[prefix + "Day" + str(index)] == "first" or propsDict[prefix + "Day" + str(index)] == "second" or propsDict[prefix + "Day" + str(index)] == "third" or propsDict[prefix + "Day" + str(index)] == "fourth" or propsDict[prefix + "Day" + str(index)] == "last":
				newdate = self.getDayIteration(year, month, propsDict[prefix + "Day" + str(index)], propsDict[prefix + "Dow" + str(index)])
				year = int(newdate.strftime("%Y"))
				month = int(newdate.strftime("%m"))
				day = int(newdate.strftime("%d"))
				
			elif propsDict[prefix + "Day" + str(index)] == "today":
				year = int(curDate.strftime("%Y"))
				month = int(curDate.strftime("%m"))
				day = int(curDate.strftime("%d"))
				
			elif propsDict[prefix + "Day" + str(index)] == "yesterday":
				newdate = dtutil.DateAdd ("days", -1, curDate)
				year = int(newdate.strftime("%Y"))
				month = int(newdate.strftime("%m"))
				day = int(newdate.strftime("%d"))
				
			elif propsDict[prefix + "Day" + str(index)] == "lastday":
				day = calendar.monthrange(year, month)
				day = day[1]
				
			else:
				day = int(propsDict[prefix + "Day" + str(index)]) # they chose a day
				
				
			# Evaluate the time
			if propsDict[prefix + "Time" + str(index)] == "any":
				hour = hour # do nothing, the default is already this
				
			elif propsDict[prefix + "Time" + str(index)] == "now": # 2.0
				hour = int(curDate.strftime("%H"))
				minute = int(curDate.strftime("%M"))
				
			else:
				time = propsDict[prefix + "Time" + str(index)]
				time = time.split(":")
				hour = int(time[0])
				minute = int(time[1])
				second = 0
				
			
			# Re-assemble the date and return it
			retstr = str(year) + "-" + "%02d" % month + "-" + "%02d" % day + " " + "%02d" % hour + ":" + "%02d" % minute + ":" + "%02d" % second
			ret = datetime.datetime.strptime (retstr, "%Y-%m-%d %H:%M:%S")
			return ret
			
		except Exception as e:
			eps.printException(e) 
			return curDate
			
		
	################################################################################
	# LIBRARY SPECIFIC METHODS
	################################################################################	
	
	#
	# Get variable date and time in user format
	#
	def getVarDateTime (self, propsDict, index):
		d = indigo.server.getTime()
		
		try:
			if eps.valueValid (propsDict, "variable" + str(index), True) and eps.valueValid (propsDict, "dtFormat" + str(index), True):
				compareString = indigo.variables[int(propsDict["variable" + str(index)])].value
				self.parent.logger.debug ("\tConverting variable '%s' date of '%s' using format '%s'" % (indigo.variables[int(propsDict["variable" + str(index)])].name, compareString, propsDict["dtFormat" + str(index)]))
				d = datetime.datetime.strptime (compareString, propsDict["dtFormat" + str(index)])
				
		except Exception as e:
			eps.printException(e) 
			
		return d	
		
	#
	# Get device state date and time in user format
	#
	def getDevStateDateTime (self, propsDict, devEx, index):
		d = indigo.server.getTime()
		
		try:
			if eps.valueValid (devEx.states, propsDict["state" + str(index)]) and eps.valueValid (propsDict, "dtFormat" + str(index), True):
				compareString = unicode(devEx.states[propsDict["state" + str(index)]])
				self.parent.logger.debug ("\tConverting state '%s' date of '%s' using format '%s'" % (propsDict["state" + str(index)], compareString, propsDict["dtFormat" + str(index)]))
				d = datetime.datetime.strptime (compareString, propsDict["dtFormat" + str(index)])
		
		except Exception as e:
			eps.printException(e) 
			
		return d		
		
	################################################################################
	# UI
	################################################################################
	
	#
	# Validate the UI
	#
	def validateDeviceConfigUi(self, valuesDict, typeId, devId):
		self.parent.logger.debug ("Validating conditions on device")
		errorDict = indigo.Dict()
		msg = ""
		
		for i in range (1, self.maxConditions + 1):
			if eps.valueValid (valuesDict, "condition" + str(i), True):
				if valuesDict["condition" + str(i)] == "device" or valuesDict["condition" + str(i)] == "devstatedatetime":
					if valuesDict["state" + str(i)] == "":
						errorDict["state" + str(i)] = "State is required"
						msg += "Condition %i is missing required state.  " % i
			
				if valuesDict["condition" + str(i)] == "variable" or valuesDict["condition" + str(i)] == "vardatetime":
					if valuesDict["variable" + str(i)] == "":
						errorDict["variable" + str(i)] = "Variable is required"
						msg += "Condition %i is missing required variable.  " % i
						
				if valuesDict["condition" + str(i)] == "datetime" or valuesDict["condition" + str(i)] == "devstatedatetime" or valuesDict["condition" + str(i)] == "vardatetime":
					if valuesDict["startDay" + str(i)] == "today" or valuesDict["startDay" + str(i)] == "yesterday": # 2.0
						if valuesDict["startDow" + str(i)] != "any":
							errorDict["startDow" + str(i)] = "Must use 'any' when using today or yesterday as the date"
							msg += "Condition %i is using '%s' as the start day and not 'any' for the day of the week.\n\n" % (i, valuesDict["startDay" + str(i)])
						
						if valuesDict["startYear" + str(i)] != "any":
							errorDict["startYear" + str(i)] = "Must use 'any' when using today or yesterday as the date"
							msg += "Condition %i is using '%s' as the start day and not 'any' for the year.\n\n" % (i, valuesDict["startDay" + str(i)])
							
						if valuesDict["startMonth" + str(i)] != "any":
							errorDict["startMonth" + str(i)] = "Must use 'any' when using today or yesterday as the date"
							msg += "Condition %i is using '%s' as the start day and not 'any' for the month.\n\n" % (i, valuesDict["startDay" + str(i)])

					if valuesDict["evaluation" + str(i)] == "between" or valuesDict["evaluation" + str(i)] == "notbetween":							
						if valuesDict["endDay" + str(i)] == "today" or valuesDict["endDay" + str(i)] == "yesterday": # 2.0
							if valuesDict["endDow" + str(i)] != "any":
								errorDict["endDow" + str(i)] = "Must use 'any' when using today or yesterday as the date"
								msg += "Condition %i is using '%s' as the end day and not 'any' for the day of the week.\n\n" % (i, valuesDict["startDay" + str(i)])
						
							if valuesDict["endYear" + str(i)] != "any":
								errorDict["endYear" + str(i)] = "Must use 'any' when using today or yesterday as the date"
								msg += "Condition %i is using '%s' as the end day and not 'any' for the year.\n\n" % (i, valuesDict["startDay" + str(i)])
							
							if valuesDict["endMonth" + str(i)] != "any":
								errorDict["endMonth" + str(i)] = "Must use 'any' when using today or yesterday as the date"
								msg += "Condition %i is using '%s' as the end day and not 'any' for the month.\n\n" % (i, valuesDict["startDay" + str(i)])
													
					if valuesDict["startDay" + str(i)] == "first" or valuesDict["startDay" + str(i)] == "second" or valuesDict["startDay" + str(i)] == "third" or valuesDict["startDay" + str(i)] == "fourth" or valuesDict["startDay" + str(i)] == "last":
						if valuesDict["startDow" + str(i)] == "any":
							errorDict["startDow" + str(i)] = "Can't use 'any' when using calculations in the day field"
							msg += "Condition %i is using '%s' as the start day but 'any' for the day of the week.\n\n" % (i, valuesDict["startDay" + str(i)])
							
					if valuesDict["endDay" + str(i)] == "first" or valuesDict["endDay" + str(i)] == "second" or valuesDict["endDay" + str(i)] == "third" or valuesDict["endDay" + str(i)] == "fourth" or valuesDict["endDay" + str(i)] == "last":
						if valuesDict["endDow" + str(i)] == "any":
							errorDict["endDow" + str(i)] = "Can't use 'any' when using calculations in the end day field"
							msg += "Condition %i is using '%s' as the end day but 'any' for the day of the week.\n\n" % (i, valuesDict["endDay" + str(i)])
							
					if valuesDict["startYear" + str(i)] == "any" and valuesDict["startMonth" + str(i)] == "any" and valuesDict["startDay" + str(i)] == "any" and valuesDict["startDow" + str(i)] == "any" and valuesDict["startTime" + str(i)] == "any":
						if valuesDict["evaluation" + str(i)] == "between" or valuesDict["evaluation" + str(i)] == "notbetween":
							if valuesDict["endYear" + str(i)] == "any" and valuesDict["endMonth" + str(i)] == "any" and valuesDict["endDay" + str(i)] == "any" and valuesDict["endDow" + str(i)] == "any" and valuesDict["endTime" + str(i)] == "any":
								errorDict["startYear" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["startMonth" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["startDay" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["startDow" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["startTime" + str(i)] = "Catch-all defeats the purpose of a condition"
								
								errorDict["endYear" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["endMonth" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["endDay" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["endDow" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["endTime" + str(i)] = "Catch-all defeats the purpose of a condition"
						
								msg += "Condition %i is using 'any' for all fields, this defeats the purpose of having a condition!  Try changing at least one to something else.\n\n" % (i)
						else:
							errorDict["startYear" + str(i)] = "Catch-all defeats the purpose of a condition"
							errorDict["startMonth" + str(i)] = "Catch-all defeats the purpose of a condition"
							errorDict["startDay" + str(i)] = "Catch-all defeats the purpose of a condition"
							errorDict["startDow" + str(i)] = "Catch-all defeats the purpose of a condition"
							errorDict["startTime" + str(i)] = "Catch-all defeats the purpose of a condition"
							
							msg += "Condition %i is using 'any' for all fields, this defeats the purpose of having a condition!  Try changing at least one to something else.\n\n" % (i)
							
					fields = ["Year", "Month", "Day", "Dow", "Time"]
					for s in fields:
						if valuesDict["evaluation" + str(i)] == "between" or valuesDict["evaluation" + str(i)] == "notbetween":
							if valuesDict["start" + s + str(i)] == "-1":
								errorDict["start" + s + str(i)] = "You must select a value"
								msg += "Condition %i field %s has an invalid value.\n\n" % (i, s)
					
							if valuesDict["end" + s + str(i)] == "-1":
								errorDict["end" + s + str(i)] = "You must select a value"
								msg += "Condition %i field End %s has an invalid value.\n\n" % (i, s)
						else:
							if valuesDict["start" + s + str(i)] == "-1":
								errorDict["start" + s + str(i)] = "You must select a value"
								msg += "Condition %i field %s has an invalid value.\n\n" % (i, s)
				
		if msg != "":
			msg = "There are problems with your conditions:\n\n" + msg
			errorDict["showAlertText"] = msg
			return (False, valuesDict, errorDict)
		
		return (True, valuesDict)
	
	#
	# Return custom list with condition options
	#
	def getConditionDateValues(self, filter="", valuesDict=None, typeId="", targetId=0):
		ret = ui.getDataList (filter, valuesDict, typeId, targetId)
		
		try:
			option = ("any", "any")
			ret.insert(0, option)
			i = 1 # where the line will go
			
			x = string.find (filter, 'monthdays')
			if x > -1:
				options = ["today|today", "yesterday|yesterday", "lastday|last day of the month", "first|first week day", "second|second week day", "third|third week day", "fourth|fourth week day", "last|last week day"]
				
				for s in options:
					data = s.split("|")
					option = (data[0], data[1])
					ret.insert(i, option)
					i = i + 1 # move the line
					
			x = string.find (filter, 'months') # 2.0
			if x > -1:
				options = ["this|this month", "last|last month"]
				
				for s in options:
					data = s.split("|")
					option = (data[0], data[1])
					ret.insert(i, option)
					i = i + 1 # move the line
					
			if filter == "years":
				options = ["current|this year", "last|last year", "next|next year"]
				
				for s in options:
					data = s.split("|")
					option = (data[0], data[1])
					ret.insert(i, option)
					i = i + 1 # move the line
					
			if filter == "dow": # 2.0
				options = ["today|today"]
				
				for s in options:
					data = s.split("|")
					option = (data[0], data[1])
					ret.insert(i, option)
					i = i + 1 # move the line
					
			if filter == "times": # 2.0
				options = ["now|now"]
				
				for s in options:
					data = s.split("|")
					option = (data[0], data[1])
					ret.insert(i, option)
					i = i + 1 # move the line
			
			line = ""
			for z in range (0, 20):
				line += unicode("\xc4", "cp437")
		
			option = ("-1", line)
			ret.insert(i, option)
			
		except Exception as e:
			eps.printException(e)
				
		return ret
	
	#
	# Collapse all conditions except for #1 (called from deviceUpdated)
	#
	def collapseAllConditions (self, dev):
		try:
			props = dev.pluginProps
			
			# See if this is a brand new device and if it is then set defaults
			if eps.valueValid (dev.pluginProps, "isNewDevice"):
				if dev.pluginProps["isNewDevice"]:
					#self.parent.logger.error("%s added, enabling conditions.  You can now re-open the device to use conditions" % dev.name)
					props["conditions"] = "none"
					props["isNewDevice"] = False
					
					for i in range (1, self.maxConditions + 1):
						props = self.setUIDefaults (props, "disabled", "onOffState")
					
					dev.replacePluginPropsOnServer(props)
					return # don't do anything else
									
			# Set up collapse options
			if eps.valueValid (dev.pluginProps, "expandConditions1"): 
				if props["expandConditions1"] == False:
					props["expandConditions1"] = True
					props["currentCondition"] = "1"
					props["noneExpanded"] = False
					
					# Check for multiple conditions to see if we need the padding
					if props["conditions"] != "none":
						for i in range (2, self.maxConditions + 1):
							if eps.valueValid (dev.pluginProps, "expandConditions" + str(i)): 
								props["multiConditions"] = True # gives us extra padding on multiple conditions
								break
							
					props = self.setUIValueVisibility (props, 1)
			else:
				# If we don't have condition 1 then we don't have any
				return
			
			for i in range (2, self.maxConditions + 1):
				if eps.valueValid (dev.pluginProps, "expandConditions" + str(i)): 
					if dev.pluginProps["expandConditions" + str(i)]: 
						props["expandConditions" + str(i)] = False
						props = self.setUIDefaults (props, "disabled", "onOffState")
					
			if props != dev.pluginProps: 
				self.parent.logger.debug ("Collapsing all conditions for %s" % dev.name)
				dev.replacePluginPropsOnServer(props)
			
		except Exception as e:
			eps.printException(e)
				
		return
	
	#
	# Add condition to pop up options
	#
	def addUIConditionMenu (self, popupList):
		try:
			if popupList is None:
				popupList = []
				
			evalList = ["none|No conditions", "alltrue|All items are true", "anytrue|Any items are true", "allfalse|All items are false", "anyfalse|Any items are false"]
			
			for s in evalList:
				eval = s.split("|")
				option = (eval[0], eval[1])
				popupList.append (option)
		
		except Exception as e:
			eps.printException(e) 
			
			popupList = []
			option = ("error", "Error in conditions, see Indigo log")
			popupList.append (option)
			
		return popupList
	
	#
	# Add evaluation to pop up options
	#
	def addUIEvals (self, popupList):
		try:
			if popupList is None:
				popupList = []
				
			evalList = ["equal|Equal to", "notequal|Not equal to", "greater|Greater than", "less|Less than", "between|Between", "notbetween|Not between", "contains|Containing", "notcontains|Not containing", "in|In", "notin|Not in"]
			
			for s in evalList:
				eval = s.split("|")
				option = (eval[0], eval[1])
				popupList.append (option)
		
		except Exception as e:
			eps.printException(e) 
			
			popupList = []
			option = ("error", "Error in evaluations, see Indigo log")
			popupList.append (option)
			
		return popupList
			
	#
	# Add conditions to pop up options
	#
	def appendUIConditions (self, popupList, type = "device"):
		try:
			type = type.lower()
			
			if popupList is None:
				popupList = []
				
			option = ("disabled", "- CONDITION DISABLED -")
			popupList.append (option)
				
			if type == "device" or type == "all":
				option = ("device", "Device state")
				popupList.append (option)
				
			if type == "variable" or type == "all":
				option = ("variable", "Variable value")
				popupList.append (option)
				
			if type == "datetime" or type == "all":
				option = ("datetime", "Date and time")
				popupList.append (option)
				
			if type == "devstatedate" or type == "all":
				option = ("devstatedatetime", "Date and time from device state")
				popupList.append (option)
								
			if type == "vardate" or type == "all":
				option = ("vardatetime", "Date and time from variable")
				popupList.append (option)
				
				
		except Exception as e:
			eps.printException(e) 
			
			popupList = []
			option = ("error", "Error in conditions, see Indigo log")
			popupList.append (option)
			
		return popupList
	
	#
	# Set up any UI defaults that we need
	#
	def setUIDefaults (self, valuesDict, defaultCondition = "disabled", defaultState = "onOffState"):
		try:
			# Make sure times are defaulted
			if eps.valueValid (valuesDict, "startTime1", True) == False:
				self.parent.logger.debug ("Setting default values")
				for i in range (1, self.maxConditions + 1):
					if eps.valueValid (valuesDict, "condition" + str(i)): valuesDict["condition" + str(i)] = defaultCondition
					if eps.valueValid (valuesDict, "evaluation" + str(i)): valuesDict["evaluation" + str(i)] = "equal"
					if eps.valueValid (valuesDict, "state" + str(i)): valuesDict["state" + str(i)] = defaultState
					if eps.valueValid (valuesDict, "startTime" + str(i)): valuesDict["startTime" + str(i)] = "08:00"
					if eps.valueValid (valuesDict, "endTime" + str(i)): valuesDict["endTime" + str(i)] = "09:00"
					if eps.valueValid (valuesDict, "startMonth" + str(i)): valuesDict["startMonth" + str(i)] = "01"
					if eps.valueValid (valuesDict, "endMonth" + str(i)): valuesDict["endMonth" + str(i)] = "02"
					if eps.valueValid (valuesDict, "startDay" + str(i)): valuesDict["startDay" + str(i)] = "01"
					if eps.valueValid (valuesDict, "endDay" + str(i)): valuesDict["endDay" + str(i)] = "15"
					if eps.valueValid (valuesDict, "startDow" + str(i)): valuesDict["startDow" + str(i)] = "0"
					if eps.valueValid (valuesDict, "endDow" + str(i)): valuesDict["endDow" + str(i)] = "6"
					if eps.valueValid (valuesDict, "startYear" + str(i)): valuesDict["startYear" + str(i)] = "any"
					if eps.valueValid (valuesDict, "endYear" + str(i)): valuesDict["endYear" + str(i)] = "any"
			
			valuesDict = self.autoCollapseConditions (valuesDict)
			valuesDict = self.showPlaceholders (valuesDict)
			
			# If everything is collapsed then show the full placeholder if conditions are enabled
			if valuesDict["currentCondition"] == "0" and valuesDict["conditions"] != "none":
				self.parent.logger.debug("Current block is 0, setting placeholder")
				valuesDict["noneExpanded"] = True
			else:
				valuesDict["noneExpanded"] = False
			
			
			#self.parent.logger.error("\n" + unicode(valuesDict))
			return valuesDict
						
		except Exception as e:
			eps.printException(e)
				
		return valuesDict
	
	#
	# Show/hide placeholder blocks for the current condition (largest to base on is device state date/time with between)
	#
	def showPlaceholders (self, valuesDict):
		try:
			if self.enablePlaceholders == False: return valuesDict
			
			cb = valuesDict["currentCondition"]
			currentBlock = int(cb)
			if currentBlock == 0: return valuesDict # nothing to do
						
			# Disable all condition blocks
			valuesDict["isDisabled"] = False
			valuesDict["placeThree"] = False
			valuesDict["placeFour"] = False
			valuesDict["placeFive"] = False
			valuesDict["placeSix"] = False 
			valuesDict["placeSeven"] = False 
			valuesDict["placeNine"] = False 
			valuesDict["placeTen"] = False 
			valuesDict["placeThirteen"] = False
			valuesDict["placeFifteen"] = False 
						
			# If there are no conditions
			if valuesDict["conditions"] == False:
				self.parent.logger.debug ("No conditions, current block is 0")
				valuesDict["currentCondition"] = "0" # it's the current condition and got collapsed, meaning all are collapsed
				return valuesDict
			
			# If it's collapsed then show that placeholder and return
			if valuesDict["expandConditions" + cb] == False:
				self.parent.logger.debug ("All blocks collapsed, current block is 0")
				valuesDict["currentCondition"] = "0" # it's the current condition and got collapsed, meaning all are collapsed
				return valuesDict
			
			valuesDict["multiConditions"] = False # Always turn it off here, save and close always turns it on

			bt = False # We have a "between" that extends things
			if valuesDict["evaluation" + cb] == "between" or valuesDict["evaluation" + cb] == "notbetween": bt = True
				
			if valuesDict["condition" + cb] == "disabled":
				valuesDict["isDisabled"] = True
				
			elif valuesDict["condition" + cb] == "timeonly" or valuesDict["condition" + cb] == "dow":
				valuesDict["placeThree"] = True
			
			elif (valuesDict["condition" + cb] == "variable" and bt == False) or valuesDict["condition" + cb] == "dateonly":
				valuesDict["placeFour"] = True
				
			elif (valuesDict["condition" + cb] == "device" and bt == False) or (valuesDict["condition" + cb] == "variable" and bt):
				valuesDict["placeFive"] = True
				
			elif (valuesDict["condition" + cb] == "device" and bt):
				valuesDict["placeSix"] = True
				
			elif (valuesDict["condition" + cb] == "datetime" and bt == False):
				valuesDict["placeSeven"] = True	
				
			elif (valuesDict["condition" + cb] == "vardatetime" and bt == False):
				valuesDict["placeNine"] = True	
				
			elif (valuesDict["condition" + cb] == "devstatedatetime" and bt == False):
				valuesDict["placeTen"] = True	
			
			elif (valuesDict["condition" + cb] == "datetime" and bt):
				valuesDict["placeThirteen"] = True	
				
			elif (valuesDict["condition" + cb] == "vardatetime" and bt):
				valuesDict["placeFifteen"] = True	
		
		except Exception as e:
			eps.printException(e)
				
		return valuesDict
	
	#
	# Auto collapse condition blocks based on what was most recently expanded
	#
	def autoCollapseConditions (self, valuesDict):
		try:
			currentBlock = int(valuesDict["currentCondition"])
			
			# Run through all conditions, if any other than the current is checked then update
			for i in range (1, self.maxConditions + 1):	
				if eps.valueValid (valuesDict, "expandConditions" + str(i)):
					if valuesDict["expandConditions" + str(i)] and i != currentBlock:
						currentBlock = i
						break
					
			# Now collapse all but the current block
			for i in range (1, self.maxConditions + 1):	
				if eps.valueValid (valuesDict, "expandConditions" + str(i)):	
					if i != currentBlock: valuesDict["expandConditions" + str(i)] = False
						
			# Hide/show fields for all unexpanded/expanded conditions
			for i in range (1, self.maxConditions + 1):	
				if eps.valueValid (valuesDict, "expandConditions" + str(i)):
					valuesDict = self.setUIValueVisibility (valuesDict, i) # also hide options
					
			# Save the current block
			self.parent.logger.debug ("Current condition block set to %i" % currentBlock)
			valuesDict["currentCondition"] = str(currentBlock)
				
		except Exception as e:
			eps.printException(e)
				
		return valuesDict	
		
	#
	# Hide or show the end value or end time
	#
	def setUIValueVisibility (self, valuesDict, index):
		try:
			# Turn off everything, we'll turn it on below
			valuesDict["hasStartValue" + str(index)] = False
			valuesDict["hasStartTime" + str(index)] = False
			valuesDict["hasStartDate" + str(index)] = False
			valuesDict["hasStartDow" + str(index)] = False
					
			valuesDict["hasEndValue" + str(index)] = False
			valuesDict["hasEndTime" + str(index)] = False
			valuesDict["hasEndDate" + str(index)] = False
			valuesDict["hasEndDow" + str(index)] = False
			
			valuesDict["hasPythonFormat" + str(index)] = False
			valuesDict["hasDevice" + str(index)] = False
			valuesDict["hasVariable" + str(index)] = False
			
			if valuesDict["conditions"] == "none": 
				#self.parent.logger.debug ("Condition checking has been turned off, disabling all condition fields")
				return valuesDict # nothing more to do, they turned off condition checking
				
			if valuesDict["expandConditions" + str(index)] == False:
				#self.parent.logger.debug ("Condition %i is collapsed" % index)
				return valuesDict # nothing more to do, they turned off condition checking
				
			if valuesDict["condition" + str(index)] == "disabled":
				#self.parent.logger.debug ("Condition %i is disabled" % index)
				return valuesDict # nothing more to do, they turned off condition checking
			
			# Turn on start values
			if valuesDict["condition" + str(index)] == "device" or valuesDict["condition" + str(index)] == "variable":
				valuesDict["hasStartValue" + str(index)] = True
				if valuesDict["condition" + str(index)] == "device": valuesDict["hasDevice" + str(index)] = True
				if valuesDict["condition" + str(index)] == "variable": valuesDict["hasVariable" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "dateonly":
				valuesDict["hasStartDate" + str(index)] = True
			
			elif valuesDict["condition" + str(index)] == "timeonly":
				valuesDict["hasStartTime" + str(index)] = True
			
			elif valuesDict["condition" + str(index)] == "dow":
				valuesDict["hasStartDow" + str(index)] = True
			
			elif valuesDict["condition" + str(index)] == "datetime":
				valuesDict["hasStartTime" + str(index)] = True
				valuesDict["hasStartDate" + str(index)] = True
			
			elif valuesDict["condition" + str(index)] == "devstatedateonly":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartDate" + str(index)] = True	
				valuesDict["hasDevice" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "devstatetimeonly":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartTime" + str(index)] = True
				valuesDict["hasDevice" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "devstatedatetime":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartTime" + str(index)] = True
				valuesDict["hasStartDate" + str(index)] = True
				valuesDict["hasDevice" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "devstatedow":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartDow" + str(index)] = True
				valuesDict["hasDevice" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "vardateonly":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartDate" + str(index)] = True	
				valuesDict["hasVariable" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "vartimeonly":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartTime" + str(index)] = True
				valuesDict["hasVariable" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "vardatetime":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartTime" + str(index)] = True
				valuesDict["hasStartDate" + str(index)] = True
				valuesDict["hasVariable" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "vardow":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartDow" + str(index)] = True
				valuesDict["hasVariable" + str(index)] = True
								
			if valuesDict["evaluation" + str(index)] == "between" or valuesDict["evaluation" + str(index)] == "notbetween":
				self.parent.logger.debug ("Condition %i requires an end value" % index)
			
				# See if we need to show or hide the end value or date/time contains value
				if valuesDict["condition" + str(index)] == "device" or valuesDict["condition" + str(index)] == "variable":
					valuesDict["hasEndValue" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "devdate" or valuesDict["condition" + str(index)] == "vardate":
					valuesDict["hasEndValue" + str(index)] = True
					valuesDict["hasPythonFormat" + str(index)] = True
									
				elif valuesDict["condition" + str(index)] == "dateonly":
					valuesDict["hasEndDate" + str(index)] = True
										
				elif valuesDict["condition" + str(index)] == "timeonly":
					valuesDict["hasEndTime" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "dow":
					valuesDict["hasEndDow" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "datetime":
					valuesDict["hasEndTime" + str(index)] = True
					valuesDict["hasEndDate" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "devstatedateonly":
					valuesDict["hasEndDate" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "devstatetimeonly":
					valuesDict["hasEndTime" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "devstatedow":
					valuesDict["hasEndDow" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "devstatedatetime":
					valuesDict["hasEndTime" + str(index)] = True
					valuesDict["hasEndDate" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "vardateonly":
					valuesDict["hasEndDate" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "vartimeonly":
					valuesDict["hasEndTime" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "vardow":
					valuesDict["hasEndDow" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "vardatetime":
					valuesDict["hasEndTime" + str(index)] = True
					valuesDict["hasEndDate" + str(index)] = True
					
				else:
					self.parent.logger.error ("Unknown between condition for %i" % index)
				
			elif valuesDict["evaluation" + str(index)] == "contains" or valuesDict["evaluation" + str(index)] == "notcontains":
				# Turn off start date fields since they aren't used here
				valuesDict["hasStartTime" + str(index)] = False
				valuesDict["hasStartDate" + str(index)] = False
				valuesDict["hasStartDow" + str(index)] = False
				
				valuesDict["hasEndValue" + str(index)] = False
				valuesDict["hasEndTime" + str(index)] = False
				valuesDict["hasEndDate" + str(index)] = False
				valuesDict["hasEndDow" + str(index)] = False
				valuesDict["hasStartValue" + str(index)] = True
				
			elif valuesDict["evaluation" + str(index)] == "in" or valuesDict["evaluation" + str(index)] == "notin": # 2.2
				if valuesDict["condition" + str(index)] == "datetime" or valuesDict["condition" + str(index)] == "devstatedatetime" or valuesDict["condition" + str(index)] == "vardatetime":
					valuesDict["hasStartTime" + str(index)] = True
					valuesDict["hasStartDate" + str(index)] = True
					valuesDict["hasStartDow" + str(index)] = True
					
				else:				
					# Turn off start date fields since they aren't used here
					valuesDict["hasStartTime" + str(index)] = False
					valuesDict["hasStartDate" + str(index)] = False
					valuesDict["hasStartDow" + str(index)] = False
				
				valuesDict["hasEndValue" + str(index)] = False
				valuesDict["hasEndTime" + str(index)] = False
				valuesDict["hasEndDate" + str(index)] = False
				valuesDict["hasEndDow" + str(index)] = False
				valuesDict["hasStartValue" + str(index)] = True
				
		
		except Exception as e:
			eps.printException(e)
				
		return valuesDict	
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		