#!/usr/bin/python

"""
This script periodically polls a google doc and updates a set of .json files in the ballot_name/data/ folder
These files get pulled by the client which correspondingly update the svg on the frontend


ISSUES:
	
"""

import time
import os
import urllib2
import shutil
import sys
import json

#these are prefixes in the room_id_translation.csv file
#each prefix generates one .json file in ./data
SITES = [
	"bbc_a", "bbc_b", "bbc_c",
	"cs_1", "cs_2",
	"boho_a", "boho_b", "boho_c", 
	"new_build_a",
		"new_build_e", "new_build_f", "new_build_g", "new_build_h", "new_build_i",  "new_build_j",
		"new_build_k", "new_build_l", "new_build_m", "new_build_n", "new_build_o", "new_build_p", 
	"wyng_a" , "wyng_b", "wyng_c", "wyng_d",
	"coote"
] 
	

#mapping of room attribute to column number
BALLOT_DOCUMENT_COLS = {
	#roomName : 0, #roomName is ASSUMED to be col 1 and not in this dict
	'roomType' : 1,
	'weeklyRent' : 2,
	'surname' : 3,
	'name' : 4,
	'crsid' : 5,
	'year' : 6,
	'license' : 7
}

#this is fed rows of the spreadsheet
#like ["BBC A01", 'BS', '\xc2\xa3106.96', 'Cooper', 'Domy', 'crsid', 'Easter', ''],
#the row layout is as set in BALLOT_DOCUMENT_COLS
class BallotSpreadsheet:
	def __init__(self):
		self.data = {}
		
	def hasKey(self, key):
		for keys in self.data:
			if keys.startswith(key):
				return True
		return False
	
	def getKey(self, key):
		for k in self.data:
			if k.startswith(key):
				return self.data[k]
				
	def toAttrDictionary(self, row):
		attrs = {}
		for attr in BALLOT_DOCUMENT_COLS:
			attrs[attr] = row[BALLOT_DOCUMENT_COLS[attr]]
		return attrs
	
	def addRow(self, row):
		if verbose:
			print "ADDING ROW TO BALLOT SPREADSHEET: " + str(row)
		self.data[row[0]] = self.toAttrDictionary(row)

	def hasBeenUpdated(self, row):
		return self.data[row[0]] != self.toAttrDictionary(row)
	
	def update(self, row):
		self.data[row[0]] = self.toAttrDictionary(row)
	
	def isTaken(self, key):
		d = self.getKey(key)
		if d['surname'].strip() == "" and d['name'].strip() == "":
			return False
		return True

	def getOccupier(self, key): 
		d = self.getKey(key)
		return d['name'] + " " + d['surname']
	
	def getWeeklyRent(self, key):
		d = self.getKey(key)
		return d['weeklyRent']
		
	def getFullCostString(self, key):
		contract = self.getContractType(key)
		if 'term' in contract.lower():
			return "30 weeks: &pound;" + str(float(self.getWeeklyRent(key).strip())*30)
		else: #calculate both easter and yearly cost
			#note on calculation: during the holidays, so for about 25 days each holiday, you pay 80% of the cost
			s = "30 week: ~&pound;" + str(float(self.getWeeklyRent(key).strip())*30)
			s += "\nEaster: ~&pound;" + str(round(float(self.getWeeklyRent(key).strip())*(30 + 0.8 * 3.5),2))
			s += "\nYear: ~&pound;" + str(round(float(self.getWeeklyRent(key).strip()) * ( 30 + 0.8*7),2))
			return s
	
	def getRoomType(self, key): #could later add a dict to convert the spreadsheet codes to the text
		d = self.getKey(key)
		return d['roomType']
	
	def getCrsid(self, key):
		d = self.getKey(key)
		return d['crsid']
	
	#this one's tricky because some rooms are term only
	#could do something that marks rooms if they're not taken yet
	#but have term contract written in (== SET)
	def getContractType(self, key):
		d = self.getKey(key)
		return d['license']
	
	def printContents(self):
		for key in self.data:
			print key, self.data[key]
		
		
#this takes the csv file as the translation between
#the ballot document room names and the SVG file room id's
#this class has no concept of which rooms are actually in the ballot
#it simply translates between values in the translation CSV file
class RoomTranslator:
	def __init__(self, roomIdTranslationFile):
		self.roomIdTranslationFile = roomIdTranslationFile
		self.data = {}
		tmp = open(self.roomIdTranslationFile).readlines()

		for line in tmp:
			d = line.strip().split(",")
			#do it in reverse for now... not sure which way is better
			self.data[d[0]] = d[1]
	
	def convertSVGId(self, id):
		if self.data.has_key(id):
			return self.data[id]
		else:
			raise Exception("ID " + id + " does not exist in ballot sheet")
		
	def printContents(self):
		print "---Printing contents of Room Translator ---"
		for key in self.data:
			print key + ": " + self.data[key]
		
	#wrote this one as a generator for fun!
	def getRoomsFromSite(self, site):
		for room in self.data:
			if room.startswith(site):
				yield room
			
			
"""
This will duplicate all the data. Might rewrite later but good enough for now
"""
class SiteDataHolder:
	def __init__(self, site, ballotDocument, roomTranslator):
		self.rooms = {}
		self.site = site
		self.ballotDocument = ballotDocument
		self.roomTranslator = roomTranslator
		#build initial data
		print "Building data for: " + site

		for room in self.roomTranslator.getRoomsFromSite(self.site):
			if verbose:
				print "\tROOM: " + room

			ballotRoomName = self.roomTranslator.convertSVGId(room)
			info = self.buildStatusJSON(ballotRoomName)
			self.rooms[room] = info
			
	#def buildStatusList(self, ballotRoomName):
	def buildStatusJSON(self, ballotRoomName):
		if self.ballotDocument.hasKey(ballotRoomName) and ballotRoomName != "":
			info = {}
			info['status'] = "occupied" if self.ballotDocument.isTaken(ballotRoomName) else "available"
			#info = ["occupied" if self.ballotDocument.isTaken(ballotRoomName) else "available"]
			info['roomName'] = ballotRoomName
			#info.append(ballotRoomName)
			info['occupier'] = self.ballotDocument.getOccupier(ballotRoomName)
#			info.append(self.ballotDocument.getOccupier(ballotRoomName))
			info['occupierCrsid'] = self.ballotDocument.getCrsid(ballotRoomName)
#			info.append(self.ballotDocument.getCrsid(ballotRoomName))
			info['roomPrice'] = self.ballotDocument.getWeeklyRent(ballotRoomName)
#			info.append(self.ballotDocument.getWeeklyRent(ballotRoomName))
			info['contractType'] = self.ballotDocument.getContractType(ballotRoomName)
#			info.append(self.ballotDocument.getContractType(ballotRoomName))
			info['roomType'] = self.ballotDocument.getRoomType(ballotRoomName)
#			info.append(self.ballotDocument.getRoomType(ballotRoomName))
			info['fullCost'] = self.ballotDocument.getFullCostString(ballotRoomName)
			return info
		else:
			info = { 'status' : "unavailable"}
			return info
		
	#note: this doesn't handle new rooms to the translation file
	def update(self):
		updated = False
		for room in self.rooms:
			ballotName = self.roomTranslator.convertSVGId(room)
			info = self.buildStatusJSON(ballotName)
			if verbose:
				print room
				print ballotName
				print info
				print "prior:"
				print self.rooms[room]
			if self.rooms[room] != info:
				updated = True
				self.rooms[room] = info
		return updated
				
	def getJSONString(self):
		if verbose:
			print self.rooms
		return json.dumps(self.rooms)


class JSONFileWriter:
	def __init__(self, sessionId):
		self.sessionId = sessionId
	def writeJSONFile(self, site, jsonString):
		print "\t\tMaking data file: " + site + ".json"

		try:
			os.mkdir(os.path.join(self.sessionId, "data"))
		except OSError: #directory already exists
			pass
		fOut = open(os.path.join(self.sessionId, "data", site + ".json"), 'w')
		fOut.write(jsonString)
		fOut.close()
	
class RoomUpdater:
	#2016
	#https://docs.google.com/spreadsheets/d/1juGIlhvuoUeVkkaxLdFCBlVStPm4psAXO1zx774aFVs/pub?gid=1332293320&single=true&output=csv
	def __init__(self, csvUrl, sessionId, roomIdTranslationFile, continueSession=False):		
		#could make this more robust easily
		self.csvUrl = csvUrl
		self.spreadsheetKey = self.extractDocumentKey(csvUrl)
		
		self.continueSession = continueSession
		self.instanceDirName = "ballot_" + sessionId

		if not self.continueSession:
			os.mkdir(self.instanceDirName)	#throws an exception caught by outer level if already exists
			
			shutil.copy("scripts_new.js", self.instanceDirName)
			self.copyHtmlFile()	#copy and edit on the way
			#shutil.copy("site.html", self.instanceDirName)
			shutil.copy("svgStyling.css", self.instanceDirName)
			shutil.copy("style.css", self.instanceDirName)
			shutil.copy(".htaccess", self.instanceDirName)
			shutil.copytree("res", os.path.join(self.instanceDirName, "res"))
	
		self.ballotDocument = BallotSpreadsheet()
		self.roomTranslator = RoomTranslator(roomIdTranslationFile)
		self.jsonSiteWriter = JSONFileWriter(self.instanceDirName)
		self.siteJsonHolders = {}
		#set up site data holders
		for site in SITES:
			self.siteJsonHolders[site] = SiteDataHolder(site, self.ballotDocument, self.roomTranslator)

		self.interrupt = False
			
	def copyHtmlFile(self):
		fIn = open("index.html")
		fOut = open(os.path.join(self.instanceDirName, "index.html"), "w")
		replaced = False #skip checking rest of lines if already replaced
		for line in fIn:
			if not replaced and "REPLACE_THIS_WITH_KEY" in line:
				print "Found key placeholder in HTML, replacing with key"
				line = line.replace("REPLACE_THIS_WITH_KEY", self.spreadsheetKey)
				replaced = True
			fOut.write(line)
		fIn.close()
		fOut.close()
	
	def extractDocumentKey(self, csvUrl):
		path = csvUrl.split('/')
		loc = path.index('d') + 1
		return path[loc]
	
	def run(self):
		print "==========Starting=========="
		while not self.interrupt:
			print "\n*Polling online spreadsheet"
			changed = self.updateBallotDocument()
			if changed:
				print "=====ballot doc has changed===="
				if verbose:
					self.ballotDocument.printContents()
				print "\n"
				for site in self.siteJsonHolders:
					siteUpdated = self.siteJsonHolders[site].update()
					print "Site " + site + " has changed: " + str(siteUpdated)
					if siteUpdated:
						self.jsonSiteWriter.writeJSONFile(site, self.siteJsonHolders[site].getJSONString())
				print "\n"
			else:
				print "No change"
			time.sleep(20)

	"""
	WARNING: this method only works in python2
	-Returns: boolean
		true indicates need to update the HTML document
		false indicates no change in the ballot document
	-TODO: could change this to return a list of ID's that have been updated
		would make it more efficient
	-NOTES:
		google drive automatically makes the exported csv rectangular
		that is if one row is 8 long and the others are 4, they are all buffered to be 8 long
	"""	
	def updateBallotDocument(self):
		updated = False
		response = urllib2.urlopen(self.csvUrl)
		csv = response.readlines()
		numCols = len(csv[0].split(","))
		info = []
		for line in csv:
			line = line.strip()
			row = line.split(",")
			#this is a big ugly...
			if len(row) < numCols: #that means we've got one of the strange split up lines
				if len(info) > 0:
					info[-1] = info[-1] + row.pop(0) #combine those rows
				info += row
				if len(info) < numCols:
					continue
			
			if info != []:
				row = [x.replace("\"", "") for x in info]	#strip out " because they cause problems later
				info = []
				
			#throw out empty lines
			if row[0] == '':
				continue
			try:
				if self.ballotDocument.hasKey(row[0]):
					if self.ballotDocument.hasBeenUpdated(row):
						self.ballotDocument.update(row)
						updated = True
				else:
					self.ballotDocument.addRow(row)
					updated = True
			except KeyError:
				print "Skipping - key error on line: \n\t" + line
			
		return updated


if __name__ == "__main__":
	args = sys.argv[1:]
	verbose = False
	cont = False
	print "number of args: " +str(len(args))
	if len(args) < 3 or len(args) > 5:
		print "Usage: <csvUrl> <sessionId> <room id translation file> [verbose true or false - default false] [continue session - default false"
	else:
		if len(args) > 3:
			verbose = True if 'true' in args[3].lower() else False
		if len(args) > 4:
			cont = True if 'true' in args[4].lower() else False
		try:
			svgUpdater = RoomUpdater(args[0], args[1], args[2], continueSession=cont)
			svgUpdater.run()
		except OSError:
			print "\nSession resources already exists, use a different one or clear"
