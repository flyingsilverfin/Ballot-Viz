#!/usr/bin/python

"""
This script will continuously run on the server and update the html file 
It will pull the ballot document from 
https://docs.google.com/spreadsheets/d/<KEY>/export?gid=0&format=csv
where <KEY> is the document ID between /d/ and /edit in normal google doc URLS
so for the 2015 year for instance that <KEY> is 1WO0PucbVNC_6wpWkGG4Ove-hlVGFfNUs3bLj_OW6sGo
"""

"""
REWRITE IN PROCESS:
	-deciding how to interweave all the translations and statuses
	
	general idea: make no changes to the SVG files
	have a JSON data file that is read by the client
	this contains:	
	{ room_id : 
		{	roomStatus: "occupied"/"open"/"unavailable"
			occupier: 	"first last",
			crsid:	"crsid",
			contract: 	"contract",
			rent: "rent",
			roomType: "room type"
		}
		...
	}
	the client side then takes this file (only if it has been updated though)
	parses it and updates each svg element with the onmouseover, onmouseout, style information
	
	questions to be answered: different json files for different sites?
			

"""

import time
import os
import urllib2
import shutil
import sys
import json

#SVG_FILE_NAMES = ["bbc-a-floor-combined.svg", "bbc-b-floor-combined.svg"]
SITES = ["bbc_a", "bbc_b"] #these are prefixes in the room_translation.csv file
#OCCUPIED_COLOR = "#FF0000" #red
#OCCUPIED_OPACITY = "0.4"
#FREE_FILL_COLOR = "none"
#FREE_FILL_OPACITY = "0"
#FREE_OUTLINE_COLOR = "#000000"
#FREE_OUTLINE_OPACITY = "1"
#FREE_FILL_COLOR = "#00FF00" #green
#FREE_FILL_OPACITY = "0.4"
#FREE_OUTLINE_COLOR = "#00FF00"
#FREE_OUTLINE_OPACITY = "0.4"


"""
styleMapping = {
	"fill:" : [OCCUPIED_COLOR, FREE_FILL_COLOR],
	"fill-opacity:" : [OCCUPIED_OPACITY, FREE_FILL_OPACITY],
	"stroke:" : [OCCUPIED_COLOR, FREE_OUTLINE_COLOR],
	"stroke-opacity:" : [OCCUPIED_OPACITY, FREE_OUTLINE_OPACITY]
}
"""



#this is fed rows of the spreadsheet
#data looks like this:
#{"BBC A01" : ['BS', '\xc2\xa3106.96', 'Cooper', 'Domy', 'crsid', 'Easter', ''],
#...}
class BallotSpreadsheet:
	MIN_COLS = 7
	def __init__(self):
		self.data = {}
	def hasKey(self, key):
		return self.data.has_key(key)
	
	def addRow(self, row):
		if len(row) < self.MIN_COLS:
			row = row + [""]*(self.MIN_COLS - len(row)) #make sure there's an appropriate minimum number to index into
			print "[buffered]",
		print "ADDING ROW TO BALLOT SPREADSHEET: " + str(row)
		self.data[row[0]] = row[1:]
	
	def hasBeenUpdated(self, row):
		return self.data[row[0]] != row[1:]
	
	def update(self, row):
		self.data[row[0]] = row[1:]
		
	def isTaken(self, key):
		d = self.data[key]
		if d[2] == "" and d[3] == "":
			return False
		return True
	
	#using these individually is going to to be ~5x slower but whatever for now
	#not being used yet anyway
	def getOccupier(self, key): 
		d = self.data[key]
		return d[3] + " " + d[2]
	
	def getRoomCost(self, key):
		d = self.data[key]
		return d[1]
	
	def getRoomType(self, key): #could later add a dict to convert the spreadsheet codes to the text
		d = self.data[key]
		return d[0]
	
	def getCrisd(self, key):
		d = self.data[key]
		return d[4]
	
	#this one's tricky because some rooms are term only
	#could do something that marks rooms if they're not taken yet
	#but have term contract written in (== SET)
	def getContractType(self, key):
		d = self.data[key]
		return d[5]
	
	def printContents(self):
		for key in self.data:
			print key, self.data[key]
		
		
#this takes the csv file as the translation between
#the ballot document room names and the SVG file room id's
#intended to be used as a singleton, really
class RoomTranslator:
	file = "room_id_translations.csv"
	def __init__(self):
		self.data = {}
		tmp = open(self.file).readlines()
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
		self.data = {}
		self.site = site
		self.ballotDocument = ballotDocument
		self.roomTranslator = roomTranslator
		#build initial data
		for room in self.roomTranslator.getRoomsFromSite(self.site):
			ballotName = self.roomTranslator.convertSVGId(room)
			info = self.buildStatusList(ballotName)
			self.data[room] = info
			
	def buildStatusList(self, ballotName):
		if self.ballotDocument.hasKey(ballotName):
			info = ["occupied" if self.ballotDocument.isTaken(ballotName) else "available"]
			info.append(ballotName)
			info.append(self.ballotDocument.getOccupier(ballotName))
			info.append(self.ballotDocument.getCrisd(ballotName))
			info.append(self.ballotDocument.getRoomCost(ballotName))
			info.append(self.ballotDocument.getContractType(ballotName))
			info.append(self.ballotDocument.getRoomType(ballotName))
			return info
		else:
			info = ["unavailable"] + [""]*6 #just to keep a consistent length
			return info
		
	#note: this doesn't handle new rooms to the translation file
	def update(self):
		updated = False
		for room in self.data:
			ballotName = self.roomTranslator.convertSVGId(room)
			info = self.buildStatusList(ballotName)
			if self.data[room] != info:
				updated = True
				self.data[room] = info
		return updated
				
	def getJSONString(self):
		print self.data
		return json.dumps(self.data)


class JSONFileWriter:
	def __init__(self, sessionId):
		self.sessionId = sessionId
	def writeJSONFile(self, site, jsonString):
		try:
			os.mkdir(os.path.join(self.sessionId, "data"))
		except OSError: #directory already exists
			pass
		fOut = open(os.path.join(self.sessionId, "data", site + ".json"), 'w')
		fOut.write("'" + jsonString + "'")
		fOut.close()
	
class RoomUpdater:
	BASEURL = "https://docs.google.com/spreadsheets/d/<KEY>/export?gid=0&format=csv"
	def __init__(self, key, sessionId):		
		#could make this more robust
		try:
			self.instanceDirName = "ballot_" + sessionId
			os.mkdir(self.instanceDirName)
		except OSError:
			self.instanceDirName = "ballot_" + sessionId + "_2"
			os.mkdir(self.instanceDirName)
	
		shutil.copy("scripts.js", self.instanceDirName)
		shutil.copy("site.html", self.instanceDirName)
		shutil.copy("svgEmbed.html", self.instanceDirName)
		#self.copyHtmlFile(self.instanceDirName) #have to write a variable into the file #NO LONGER NEEDED
		shutil.copy("style.css", self.instanceDirName)
		shutil.copytree("res", os.path.join(self.instanceDirName, "res"))
	
		self.ballotDocument = BallotSpreadsheet()
		self.roomTranslator = RoomTranslator()
		self.jsonSiteWriter = JSONFileWriter(self.instanceDirName)
		self.siteJsonHolders = {}
		#set up site data holders
		for site in SITES:
			self.siteJsonHolders[site] = SiteDataHolder(site, self.ballotDocument, self.roomTranslator)
		self.spreadsheetKey = key
		self.docUrl = RoomUpdater.BASEURL.replace("<KEY>", key)
		print self.docUrl
		self.interrupt = False #might need it sometime...

	def run(self):
		while not self.interrupt:
			changed = self.updateBallotDocument()
			
			if changed:
				print "=====ballot doc has changed===="
				self.ballotDocument.printContents()
				print "\n"
				for site in self.siteJsonHolders:
					siteUpdated = self.siteJsonHolders[site].update()
					if siteUpdated:
						self.jsonSiteWriter.writeJSONFile(site, self.siteJsonHolders[site].getJSONString())
				print "\n"
			time.sleep(5)

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
		response = urllib2.urlopen(self.docUrl)
		csv = response.readlines()
		numCols = len(csv[0].split(","))
		info = []
		for line in csv:
			line = line.strip()
			row = line.split(",")
			if len(row) < numCols: #that means we've got one of the strange split up lines
				info += row
				continue
			if info != []:
				row = info[:]
				info = []
			if self.ballotDocument.hasKey(row[0]):
				if self.ballotDocument.hasBeenUpdated(row):
					self.ballotDocument.update(row)
					updated = True
			else:
				self.ballotDocument.addRow(row)
				updated = True
		return updated

		
if __name__ == "__main__":
	args = sys.argv[1:]
	svgUpdater = RoomUpdater(args[0], args[1])
	svgUpdater.run()