#!/usr/bin/python

"""
This script will continuously run on the server and update the html file 
It will pull the ballot document from 
https://docs.google.com/spreadsheets/d/<KEY>/export?gid=0&format=csv
where <KEY> is the document ID between /d/ and /edit in normal google doc URLS
so for the 2015 year for instance that <KEY> is 1WO0PucbVNC_6wpWkGG4Ove-hlVGFfNUs3bLj_OW6sGo
"""

import time
import os
import urllib2
import shutil
import sys

SVG_FILE_NAMES = ["bbc-a-floor-combined.svg", "bbc-b-floor-combined.svg"]
OCCUPIED_COLOR = "#FF0000"
OCCUPIED_OPACITY = "0.4"
FREE_FILL_COLOR = "none"
FREE_FILL_OPACITY = "0"
FREE_OUTLINE_COLOR = "#000000"
FREE_OUTLINE_OPACITY = "1"

styleMapping = {
	"fill:" : [OCCUPIED_COLOR, FREE_FILL_COLOR],
	"fill-opacity:" : [OCCUPIED_OPACITY, FREE_FILL_OPACITY],
	"stroke:" : [OCCUPIED_COLOR, FREE_OUTLINE_COLOR],
	"stroke-opacity:" : [OCCUPIED_OPACITY, FREE_OUTLINE_OPACITY]
}



#this is fed rows of the spreadsheet
#data looks like this:
#{"BBC A01" : ['BS', '\xc2\xa3106.96', 'Cooper', 'Domy', 'crsid', 'Easter', ''],
#...}
class BallotSpreadsheet:
	def __init__(self):
		self.data = {}
	def hasKey(self, key):
		return self.data.has_key(key)
	
	def addRow(self, row):
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

class SVGUpdater:
	#shared variables (shouldn't be >1 instance of this though, yet)
	docUrl = "https://docs.google.com/spreadsheets/d/<KEY>/export?gid=0&format=csv"
	
	def __init__(self, key, sessionId):
		self.ballotDocument = BallotSpreadsheet()
		self.roomTranslator = RoomTranslator()
		self.roomTranslator.printContents()
		self.spreadsheetKey = key
		self.docUrl = self.docUrl.replace("<KEY>", key)
		self.interrupt = False #can set this from externally to quit if necessary for some reason
		#TODO implement some sort of check to make sure it's valid
		
		#could make this more robust
		try:
			self.instanceDirName = "ballot_" + sessionId
			os.mkdir(self.instanceDirName)
		except OSError:
			self.instanceDirName = "ballot_" + sessionId + "_2"
			os.mkdir(self.instanceDirName)
		
		shutil.copy("scripts.js", self.instanceDirName)
		self.copyHtmlFile(self.instanceDirName) #have to write a variable into the file
		shutil.copy("style.css", self.instanceDirName)
		shutil.copytree("res", os.path.join(self.instanceDirName, "res"))
		
		
	def copyHtmlFile(self, dirName):
		fIn = open("site.html")
		fOut = open(os.path.join(dirName, "site.html"), "w")
		replaced = False #skip checking rest of lines if already replaced
		for line in fIn:
			if not replaced and "var instanceDirectory = \"INSTANCE_DIRECTORY\"" in line:
				line = line.replace("\"INSTANCE_DIRECTORY\"", "\"" + dirName + "\"")
				replaced = True
			fOut.write(line)
		fIn.close()
		fOut.close()
		
	def run(self):
		while not self.interrupt:
			changed = self.updateBallotDocument()
			self.ballotDocument.printContents()
			print changed
			if changed:
				self.rewriteSVGFiles()
			time.sleep(5)
	
	def rewriteSVGFiles(self):
		"""
		for now I just rewrite all the SVG files.
		in the future it could be made much more efficient by only
		rewriting the svg files that actually need changes
		"""
		for svg in SVG_FILE_NAMES:
			print "=====Processing: " + svg  + "======"
			svgData = open(os.path.join("res", svg)).readlines() #rewrite from the original source
			#could also be done much more efficiently than reading whole thing into memory
			fOut = open(os.path.join(self.instanceDirName, "res", svg), "w")
			#ALL OF THIS ASSUMES ALL THE PATHS ARE LISTED ADJACENT
			#TODO: Will probably have to make up a better way of processing the svg soon
			dataBlock = []
			found = False
			for i in range(len(svgData)):
				#print svgData[i]
				if "<path" in svgData[i]:
					if not found: #eg first <path> found
						for k in dataBlock: #not a block we want
							fOut.write(k)
						found = True #now we are in the <path>'s
					else: #just finished reading a path
						pathElement = dataBlock
						styleRow = -1
						idRow = -1
						#The following are here from when I wanted to check whether these events are already added
						#now assuming they aren't. will write a README
						#mouseoutRow = -1
						#mouseoverRow = -1
						print "------------------"
						for j in range(len(pathElement)):
							print pathElement[j]

							if "style=" in pathElement[j] and styleRow == -1:
								styleRow = j
							if "id=" in pathElement[j] and idRow == -1:
								idRow = j
							if "onmouseout=" in pathElement[j] and mouseoutRow == -1:
								mouseoutRow = j
							if "onmouseover=" in pathElement[j] and mouseoverRow == -1:
								mouseoverRow = j
						#now we know where the style and id are
						id = pathElement[idRow].split("\"")[-2]
						print "IdRow: " + str(idRow) + ", ID: " + id
						styles = pathElement[styleRow].split("=")
						stylePrefix = styles[0]
						styles = styles[1].split(";")
						ballotId = ""
						try:
							ballotId = self.roomTranslator.convertSVGId(id)
						except Exception:
							print "EXCEPTION CONVERTING " + id + " INTO BALLOT ROOM ID"
							#there should be some kind of break from the normal flow here
							#that would be good style but for now i'm just trying to get something to work
					
						"""
						#have to adjust the style depending on the situation
						#following could be cut in half by getting rid of overall IF and using inline if's to place the colors
						#also need to combine this with checking to make sure each property is actually found (maybe boolean list)
						#	===> DO ABOVE ALL AT THE SAME TIME
						if self.ballotDocument.hasKey(ballotId):
							if self.ballotDocument.isTaken(ballotId): #occupied
								for j in range(len(styles)):
									if "fill:" in styles[j]:
										styles[j] = "fill:"+OCCUPIED_COLOR
									if "fill-opacity:" in styles[j]:
										styles[j] = "fill-opacity:"+OCCUPIED_OPACITY
									if "stroke:" in styles[j]:
										styles[j] = "stroke:" + OCCUPIED_COLOR
									if "stroke-opacity:" in styles[j]:
										styles[j] = "stroke-opacity:" + OCCUPIED_OPACITY
							else: #not occupied
								for j in range(len(styles)):
									if "fill:" in styles[j]:
										styles[j] = "fill:"+FREE_FILL_COLOR
									if "fill-opacity:" in styles[j]:
										styles[j] = "fill-opacity:" + FREE_FILL_OPACITY
									if "stroke:" in styles[j]:
										styles[j] = "stroke:"+FREE_OUTLINE_COLOR
									if "stroke-opacity:" in styles[j]:
										styles[j] = "stroke-opacity:" + FREE_OUTLINE_OPACITY
						"""

						#---begin adjust styles---
						# have to adjust the styles depending on the situation
						if self.ballotDocument.hasKey(ballotId):
							occ = self.ballotDocument.isTaken(ballotId)
							#need to keep track of which properties have been found/are already there
							propsFound = dict(zip(styleMapping.keys(), [False] * len(styleMapping)))
							for j in range(len(styles)):	#iterate through the list of style elements
								for prop in styleMapping:	#if that property is one we need to change
									if prop in styles[j]:
										styles[j] = prop + styleMapping[prop][0 if occ else 1] #adjust property
										propsFound[prop] = True	#record we have changed it

							for prop in propsFound:	#now we need to add all the properties that weren't present already
								if not propsFound[prop]:
									#insert into the middle of styles because end and beginning have things like "
									styles.insert(int(len(styles)/2), prop + styleMapping[prop][0 if occ else 1])
							
							styles[-1] += "\"\n"
							
							#add mouseout 
							pathElement.insert(int(len(pathElement)/2), "onmouseout=\"top.hideTooltip()\"\n")
							#addmouseover
							params = "evt,&quot;" + "&quot;,&quot;".join([self.ballotDocument.getOccupier(ballotId), self.ballotDocument.getContractType(ballotId),
								self.ballotDocument.getRoomCost(ballotId), self.ballotDocument.getRoomType(ballotId)])
							pathElement.insert(int(len(pathElement)/2), "onmouseover=\"top.showTooltip("+params+"&quot;)\"\n")
						else:
							print "room not found in BallotSpreadsheet: " +ballotId
							#TODO: If it's not found, it might have been edited by accident
							#might make sense to do similar to above "else" close above
						print styles
						#this checking if we've lost a " feels really hacky
						styleString = ";".join(styles)
						if not styleString.startswith("\""): #if we lost a quote somehow...
							styleString = "\"" + styleString
						styleString = stylePrefix + "=" + styleString
						pathElement[styleRow] = styleString
						print "styleString: " + styleString
						
						for k in pathElement:
							fOut.write(k)
					dataBlock = [] #RESET in ANY CASE
				if "<path" in svgData[i]:
					print svgData[i]
				dataBlock.append(svgData[i])
			#now we have to write out the remaining dataBlock
			for k in dataBlock:
				fOut.write(k)
			fOut.close()

	"""
	WARNING: this method only works in python2
	-Returns: boolean
		true indicates need to update the HTML document
		false indicates no change in the ballot document
	-TODO: could change this to return a list of ID's that have been updated
		would make it more efficient
	"""	
	def updateBallotDocument(self):
		updated = False
		response = urllib2.urlopen(self.docUrl)
		csv = response.readlines()
		for line in csv:
			line = line.strip()
			row = line.split(",")
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
	svgUpdater = SVGUpdater(args[0], args[1])
	svgUpdater.run()