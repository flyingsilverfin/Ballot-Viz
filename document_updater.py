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
		"new_build_e", "new_build_f", "new_build_g", "new_build_h", "new_build_i",  "new_build_j_",
		"new_build_k", "new_build_l", "new_build_m", "new_build_n", "new_build_o", "new_build_p", 
	"wyng_a" , "wyng_b", "wyng_c", "wyng_d"
] 
	

#this is fed rows of the spreadsheet
#data looks like this:
#{"BBC A01" : ['BS', '\xc2\xa3106.96', 'Cooper', 'Domy', 'crsid', 'Easter', ''],
#...}
class BallotSpreadsheet:
	MIN_COLS = 7
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
		d = self.getKey(key)
		if d[2].strip() == "" and d[3].strip() == "":
			return False
		return True

	def getOccupier(self, key): 
		d = self.getKey(key)
		return d[3] + " " + d[2]
	
	def getRoomCost(self, key):
		d = self.getKey(key)
		return d[1]
	
	def getRoomType(self, key): #could later add a dict to convert the spreadsheet codes to the text
		d = self.getKey(key)
		return d[0]
	
	def getCrisd(self, key):
		d = self.getKey(key)
		return d[4]
	
	#this one's tricky because some rooms are term only
	#could do something that marks rooms if they're not taken yet
	#but have term contract written in (== SET)
	def getContractType(self, key):
		d = self.getKey(key)
		return d[5]
	
	def printContents(self):
		for key in self.data:
			print key, self.data[key]
		
		
#this takes the csv file as the translation between
#the ballot document room names and the SVG file room id's
#intended to be used as a singleton, really but not a big deal otherwise
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
		self.data = {}
		self.site = site
		self.ballotDocument = ballotDocument
		self.roomTranslator = roomTranslator
		#build initial data
		print "SITE: " + site

		for room in self.roomTranslator.getRoomsFromSite(self.site):
			print "\tROOM: " + room

			ballotName = self.roomTranslator.convertSVGId(room)
			info = self.buildStatusList(ballotName)
			self.data[room] = info
			
	def buildStatusList(self, ballotName):
		if self.ballotDocument.hasKey(ballotName) and ballotName != "":
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
	def __init__(self, csvUrl, sessionId, roomIdTranslationFile):		
		#could make this more robust easily
		try:
			self.instanceDirName = "ballot_" + sessionId
			os.mkdir(self.instanceDirName)
		except OSError:
			self.instanceDirName = "ballot_" + sessionId + "_2"
			os.mkdir(self.instanceDirName)
	
		self.csvUrl = csvUrl
		self.spreadsheetKey = self.extractDocumentKey(csvUrl)

		shutil.copy("scripts.js", self.instanceDirName)
		self.copyHtmlFile()	#copy and edit on the way
		#shutil.copy("site.html", self.instanceDirName)
		shutil.copy("svgStyling.css", self.instanceDirName)
		shutil.copy("style.css", self.instanceDirName)
		shutil.copytree("res", os.path.join(self.instanceDirName, "res"))
	
		self.ballotDocument = BallotSpreadsheet()
		self.roomTranslator = RoomTranslator(roomIdTranslationFile)
		self.jsonSiteWriter = JSONFileWriter(self.instanceDirName)
		self.siteJsonHolders = {}
		#set up site data holders
		for site in SITES:
			self.siteJsonHolders[site] = SiteDataHolder(site, self.ballotDocument, self.roomTranslator)
		self.interrupt = False #might need it sometime...

	def copyHtmlFile(self):
		fIn = open("site.html")
		fOut = open(os.path.join(self.instanceDirName, "site.html"), "w")
		replaced = False #skip checking rest of lines if already replaced
		for line in fIn:
			if not replaced and "REPLACE_THIS_WITH_KEY" in line:
				print "FOUND ----- "
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
			print "\n*Going in to update ballot document"
			changed = self.updateBallotDocument()
			print "*Finished upating ballot document"
			print "*Going to update relevant data"
			if changed:
				print "=====ballot doc has changed===="
				self.ballotDocument.printContents()
				print "\n"
				for site in self.siteJsonHolders:
					siteUpdated = self.siteJsonHolders[site].update()
					print "Site " + site + " has changed: " + str(siteUpdated)
					if siteUpdated:
						self.jsonSiteWriter.writeJSONFile(site, self.siteJsonHolders[site].getJSONString())
				print "\n"
			print "sleeping 5 sec"
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
	if len(args) != 3:
		print "Usage: <csvUrl> <sessionId> <room id translation file>"
	else:
		svgUpdater = RoomUpdater(args[0], args[1], args[2])
		svgUpdater.run()	
