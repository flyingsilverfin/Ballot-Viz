var currentlySelected = "bbc_a";
//the following object translates between the site button's ID and that site's URI

var siteFilenames = {
	"bbc_a" : 'bbc-a-floor-combined.svg',
	"bbc_b" : 'bbc-b-floor-combined.svg',
	"bbc_c" : 'bbc-c-floor-combined.svg',
	"cs_1" : 'cs-first-floor-combined.svg',
	"cs_2" : 'cs-second-floor-combined.svg',
	"boho_a" : 'boho-a-floor-combined.svg',
	"boho_b" : 'boho-b-floor-combined.svg',
	"boho_c" : 'boho-c-floor-combined.svg', 
	"new_build-a" : 'new-build-a-stair_combined.svg',
	"new_build_e-f-g-h-i-j" : 'new-build-e-f-g-h-i-j-stair_combined.svg',
	"new_build_k-l-m-n-o-p" : 'new-build-k-l-m-n-o-p-stair_combined.svg',
	"wyng_a" : 'wyng-a-floor-combined.svg',
	"wyng_b" : 'wyng-b-floor-combined.svg',
	"wyng_c" : 'wyng-c-floor-combined.svg',
	"wyng_d" : 'wyng-d-floor-combined.svg'
}

var siteData = {
	"bbc_a" : [],
	"bbc_b" : [],
	"bbc_c" : [],
	"cs_1" : [],
	"cs_2" : [],
	"boho_a" : [],
	"boho_b" : [],
	"boho_c" : [],
	"new_build-a" : [],
	"new_build_e-f-g-h-i-j" : [],
	"new_build_k-l-m-n-o-p" : [],
	"wyng_a" : [],
	"wyng_b" : [],
	"wyng_c" : [],
	"wyng_d" :[]
}

var siteEtags = {
	"bbc_a" : "-1",
	"bbc_b" : "-1",
	"bbc_c" : "-1",
	"cs_1" :"-1",
	"cs_2" : "-1",
	"boho_a" : -1,
	"boho_b" : -1,
	"boho_c" : -1,
	"new_build-a" : -1,
	"new_build_e-f-g-h-i-j" : -1,
	"new_build_k-l-m-n-o-p" : -1,
	"wyng_a" : -1,
	"wyng_b" : -1,
	"wyng_c" : -1,
	"wyng_d" :-1
}

function loaded() {
	var im = document.getElementById("svg_image");
	var container = document.getElementById("svg_container");
	im.width = container.clientWidth;
	loadSVG(currentlySelected);
	updateAll();
	setInterval(updateAll, 5000);	
}

function updateAll() {
	for (var site in siteData) {
		console.log("going to update: " + site);
		updateSite(site)
	}
}

function updateSite(site) {
	var httpRequest = new XMLHttpRequest();
	var priorEtag = siteEtags[site];
	httpRequest.onreadystatechange = function() {
		var newEtag = httpRequest.getResponseHeader("etag");
		if (httpRequest.readyState == 4 && httpRequest.status == 200 && newEtag != priorEtag) {
			//this means request is ready and the file is new!
			siteEtags[site] = newEtag;
			console.log("RESPONSE: " + httpRequest.response);
			updatedData(site, JSON.parse(httpRequest.response));
		}
	}
	console.log("getting: data/" + site +".json");
	httpRequest.open("GET", "data/" + site + ".json", true);
	httpRequest.send(null);
}

//this gets called when we know the data has changed
function updatedData(site, dataObject) {
	//might be fun to do a scrolling changes thing
	var diffs = getDifferences(siteData[site], dataObject);
	showUpdates(diffs);
	siteData[site] = dataObject;
	if (currentlySelected == site) {
		updateSvgData(currentlySelected);
	} else {
		var notifier = document.getElementById(site).getElementsByClassName("indicator")[0];
		notifier.style.backgroundColor = "blue";
		notifier.parentElement.title = "has changes";
	}
}

//roomDifferences is structured as:
//{ room : ["John smith", "BBC A01", "available", "occupied"] ...}
//			^^ new occupier	^^room	   ^^old status  ^^new status
function showUpdates(roomDifferences) {
	console.log("\t\t Going to write up differences");
	var oldstatus = "";
	var newstatus = ""; //No idea if this help reduce number of variable allocations in javascript... probably optimizied away
	var updatesPane = document.getElementById("updates_pane");

	for (var room in roomDifferences) {
		oldstatus = roomDifferences[room][2];
		newstatus = roomDifferences[room][3];
		if (oldstatus == "available" && newstatus == "occupied") {
			var div = document.createElement("div")
			div.setAttribute("class", "updates_row updates_taken");
			div.innerHTML = roomDifferences[room][0]  + " has taken " + roomDifferences[room][1].toUpperCase();
			updatesPane.insertBefore(div, updatesPane.firstChild);	
		} else if (oldstatus == "occupied" && newstatus == "available") {
			var div = document.createElement("div")
			div.setAttribute("class", "updates_row updates_freed");
			div.innerHTML = roomDifferences[room][1] + " has become available";
			updatesPane.insertBefore(div, updatesPane.firstChild);	
		} else {
			//do nothing because it's some odd case
		}
	}
}

function getDifferences(oldRoomData, newRoomData) {
	var changedRooms = {}
	for (var r in oldRoomData) {
		var oldData = oldRoomData[r];
		var newData = newRoomData[r];
		if (oldData[0] != newData[0]) {
			changedRooms[r] = [newData[2], newData[1], oldData[0], newData[0]];
		}
	}
	return changedRooms;
}

//only operates on the current loaded svg
function updateSvgData(currentSite) {
	var dataObject = siteData[currentSite];
	console.log(siteData);
	var svg = document.getElementById("svg_image").contentDocument;
	for (var room in dataObject) {
		console.log("Room being processed: " + room);
		var r = svg.getElementById(room);
		var roomStatus = dataObject[room][0];
		console.log("\tRoom status: " + roomStatus);
		if (roomStatus == "unavailable") {
			console.log("\t\t unavailable selected");
			r.setAttribute("style","");
			//restyle
			r.setAttribute("class", "unavailable");
		} else if ( roomStatus == "available") {
			console.log("\t\t available selected");
			r.setAttribute('onmouseout','top.hideTooltip()');
			r.setAttribute('onmouseover', 'top.showTooltip(evt,"'+ 
			dataObject[room][1] + 
			'","' + dataObject[room][2] + 
			'","' + dataObject[room][3] + 
			'","' + dataObject[room][4] + 
			'","' + dataObject[room][5] + 
			'","' + dataObject[room][6] + '")');
			r.setAttribute("style", "");
			r.setAttribute("class", "available");
		} else if (roomStatus == "occupied") {
			console.log("\t\t occupied selected");
			r.setAttribute('onmouseout','top.hideTooltip()');
			r.setAttribute('onmouseover','top.showTooltip(evt,"'+ 
			dataObject[room][1] + 
			'","' + dataObject[room][2] + 
			'","' + dataObject[room][3] + 
			'","' + dataObject[room][4] + 
			'","' + dataObject[room][5] + 
			'","' + dataObject[room][6] + '")');
			r.setAttribute("style", "");
			r.setAttribute("class", "occupied");
		}
	}	
}


function showTooltip(elem, room, occupant, crisd, rent, contractType, roomType) {
	var im = document.getElementById("svg_image");
	//calculate the offsets of the image initially
	var sidebar = document.getElementById("sidebar");
	var sidebarWidth = sidebar.getBoundingClientRect().width;
	var header = document.getElementById("header_container");
	var headerHeight = header.getBoundingClientRect().height;
	var imLeft = im.getBoundingClientRect().left;
	var imTop = im.getBoundingClientRect().top;
	document.getElementById("room").innerHTML = room;
	document.getElementById("occupant").innerHTML = occupant;
	document.getElementById("crsid").innerHTML = "("+crisd+")";
	document.getElementById("contract_type").innerHTML = contractType;
	rent = document.getElementById("rent").innerHTML = rent;
	roomType = document.getElementById("room_type").innerHTML = roomType;
	var tooltip = document.getElementById("tooltip");
	var elemPos = elem.target.getBoundingClientRect(); //this is constant depending on zoom level
	var posLeft = (imLeft + elemPos.left - sidebarWidth + elemPos.width/2 - tooltip.getBoundingClientRect().width/2) + "px";
	var posTop = (imTop + elemPos.top - headerHeight - tooltip.getBoundingClientRect().height - 10) + "px";
	tooltip.style.left = posLeft;
	tooltip.style.top = posTop;
	tooltip.style.visibility = "visible";
	tooltip.zIndex = "5";
}

function hideTooltip() {
	var tooltip = document.getElementById("tooltip");
	tooltip.style.visibility = "hidden";
	tooltip.zIndex = "-5";
}

function zoomIn() {
	var im = document.getElementById("svg_image");
	//im.height = im.height * 1.1;
	im.width = im.width * 1.1;
}

function zoomOut() {
	var im = document.getElementById("svg_image");
	//im.height = im.height * 0.9;
	im.width = im.width * 0.9;
}

//from parameters is DOM node that is clicked on
//parent ID is site to load!
function loadSVG(from) {
	var siteName = from.parentElement.id;	

	console.log("loading: " +siteName);
	var svgContainer = document.getElementById("svg_container");
	var im = document.getElementById("svg_image");
	//adding some sort of timestamp forces browser to redraw image, otherwise wouldn't show up half the time (interesting)
	// + "?time="+Date.now()
	//DECISION: Adding it uses up much more bandwidth for each switch.
	//	On the other hand it seems to make firefox render the svg properly each time...
	//	not sure if chrome has this issue
	im.data = "res/" + siteFilenames[siteName]; //CANNOT HAVE A PRECEDING SLASH (think regular unix)
	var notifier = document.getElementById(siteName).getElementsByClassName("indicator")[0];
	notifier.style.backgroundColor = "lightgreen";
	notifier.parentElement.title = "up to date";
	document.getElementById(currentlySelected).style.backgroundColor = "#E0E0E0";
	currentlySelected = siteName;
	var selector = document.getElementById(currentlySelected);
	selector.style.backgroundColor = "white";
	//we can only do operations on the svg once loaded!
	im.addEventListener("load", function() {
		var linkElm = im.contentDocument.createElementNS("http://www.w3.org/1999/xhtml", "link");
		linkElm.setAttribute("href", "../svgStyling.css");
		linkElm.setAttribute("type", "text/css");
		linkElm.setAttribute("rel", "stylesheet");
		im.contentDocument.getElementsByTagName("defs")[0].appendChild(linkElm);
		console.log(linkElm);
		updateSvgData(currentlySelected);
	});
}
