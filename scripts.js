var currentlySelected = "bbc_a";
//the following object translates between the site button's ID and that site's URI

var siteFilenames = {
	"bbc_a" : 'bbc-a-floor-combined.svg',
	"bbc_b" : 'bbc-b-floor-combined.svg'
}

var siteData = {
	"bbc_a" : [],
	"bbc_b" : []
}

var siteEtags = {
	"bbc_a" : "-1",
	"bbc_b" : "-1",
}

function loaded() {
	//set a global so we don't have to retrieve it all the time
	//basically the entire page is static except the embedded iframe
	embedded = document.getElementById("svg_embed").contentDocument;
	var im = embedded.getElementById("svg_image");
	var container = embedded.getElementById("svg_container");
	im.width = container.clientWidth;
	var selector = document.getElementById(currentlySelected); //initially selected
	selector.style.backgroundColor = "white";
	updateAll();
	setInterval(updateAll, 5000);	
}

function updateAll() {
	for (site in siteData) {
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
			updateData(site, JSON.parse(httpRequest.response))
		}
	}
	httpRequest.open("GET", "data/" + site + ".json", true);
	httpRequest.send(null);
}

function updateData(site, dataObject) {
	siteData[site] = dataObject;
	if (currentlySelected == site) {
		updateSvgData(dataObject);
	} else {
		var notifier = document.getElementById(site).getElementsByClassName("indicator")[0];
		notifier.style.backgroundColor = "blue";
	}
}

//only operates on the current loaded svg
function updateSvgData(dataObject) {
	var svg = embedded.getElementById("svg_image").contentDocument;
	for (room in dataObject) {
		var r = svg.getElementById(room);
		roomStatus = dataObject[room][0];
		if (dataObject[room][0] == "unavailable") {
			r.style = "";
			//restyle
			r.setAttribute("class", "unavailable");
		} else if ( dataObject[room] == "available") {
			r.onmouseout = 'top.hideTooltip()';
			r.onmouseover = 'top.showTooltip(elem,"'+ 
			'"' + dataObject[room][1] + 
			'","' + dataObject[room][2] + 
			'","' + dataObject[room][3] + 
			'","' + dataObject[room][4] + 
			'","' + dataObject[room][5] + 
			'","' + dataObject[room][6] + '")';
			r.style = "";
			r.setAttribute("class", "available");
		} else if (dataObject[room] == "occupied") {
			r.onmouseout = 'top.hideTooltip()';
			r.onmouseover = 'top.showTooltip(elem,"'+ 
			'"' + dataObject[room][1] + 
			'","' + dataObject[room][2] + 
			'","' + dataObject[room][3] + 
			'","' + dataObject[room][4] + 
			'","' + dataObject[room][5] + 
			'","' + dataObject[room][6] + '")';
			r.style = "";
			r.setAttribute("class", "occupied");
		}
	}	
}


function showTooltip(elem, room, occupant, camCrsid, rent, contractType, roomType) {
	var im = embedded.getElementById("svg_image");
	//calculate the offsets of the image initially
	var sidebar = document.getElementById("sidebar");
	var sidebarWidth = sidebar.getBoundingClientRect().width;
	var header = document.getElementById("header_container");
	var headerHeight = header.getBoundingClientRect().height;
	
	var imLeft = im.getBoundingClientRect().left;
	var imTop = im.getBoundingClientRect().top;
		
	document.getElementById("room").innerHTML = room;
	document.getElementById("occupant").innerHTML = occupant;
	
	document.getElementById("crsid").innerHTML = "(" + camCrsid + ")";

	document.getElementById("contract_type").innerHTML = contractType;
	rent = document.getElementById("rent").innerHTML = rent;
	roomType = document.getElementById("room_type").innerHTML = roomType;
	
	var tooltip = document.getElementById("tooltip");
	
	var elemPos = elem.target.getBoundingClientRect(); //this is constant depending on zoom level
	
	var posLeft = (imLeft + elemPos.left - tooltip.getBoundingClientRect().width/2 + elemPos.width/2) + "px";
	var posTop = (imTop + elemPos.top - tooltip.getBoundingClientRect().height - 10) + "px";
	

	tooltip.style.left = posLeft;
	tooltip.style.top = posTop;
	tooltip.style.visibility = "visible";
	tooltip.zIndex = "5";
}

function zoomIn() {
	var im = embedded.getElementById("svg_image");
	//im.height = im.height * 1.1;
	im.width = im.width * 1.1;
}

function zoomOut() {
	var im = embedded.getElementById("svg_image");
	//im.height = im.height * 0.9;
	im.width = im.width * 0.9;
}



function loadSVG(siteName) {
	console.log("loading: " +siteName);
	var svgContainer = embedded.getElementById("svg_container");
	var im = embedded.getElementById("svg_image");
	//adding some sort of timestamp forces browser to redraw image, otherwise wouldn't show up half the time (interesting)
	im.data = "res/" + siteFilenames[siteName]; //CANNOT HAVE A PRECEDING SLASH (think regular unix)
	var notifier = document.getElementById(site).getElementsByClassName("indicator")[0];
	notifier.style.backgroundColor = "lightgreen";
	document.getElementById(currentlySelected).style.backgroundColor = "#E0E0E0";
	currentlySelected = siteName;
	var selector = document.getElementById(currentlySelected);
	selector.style.backgroundColor = "white";
}
