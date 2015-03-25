var currentlySelected = "bbc_a";

function loaded() {
	var im = document.getElementById("svg_image");
	var container = document.getElementById("svg_container");
	im.width = container.clientWidth;
	var selector = document.getElementById(currentlySelected); //initially selected
	selector.style.backgroundColor = "white";
}

function loadSVG(location, siteDivId) {
	var im = document.getElementById("svg_image");
	//adding some sort of timestamp forces browser to redraw image, otherwise wouldn't show up half the time
	im.data = BASE_URL + instanceDirectory + "/res/" + location + "?timestamp" + Date.now();
	document.getElementById(currentlySelected).style.background = "#E0E0E0";
	currentlySelected = siteDivId;
	var selector = document.getElementById(currentlySelected);
	selector.style.backgroundColor = "white";
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

function showTooltip(elem, room, occupant, crisd, contractType, rent, roomType) {
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
	document.getElementById("crsid").innerHTML = crisd
	document.getElementById("contract_type").innerHTML = contractType;
	rent = document.getElementById("rent").innerHTML = rent;
	roomType = document.getElementById("room_type").innerHTML = roomType;
	
	var tooltip = document.getElementById("tooltip");
	
	var elemPos = elem.target.getBoundingClientRect(); //this is constant depending on zoom level
	var posLeft = (imLeft + elemPos.left - sidebarWidth  + elemPos.width/2 - tooltip.getBoundingClientRect().width/2) + "px";
	var posTop = (imTop + elemPos.top - headerHeight - tooltip.getBoundingClientRect().height - 10) + "px";
	//var posLeft = (elemPos.left + 50) + "px"; //TODO: replace the hardcoded 50 addition
	//var posTop = (elemPos.top - 50) + "px";
	

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

/*
function rotateCW() {

}

function rotateCCW() {

}*/