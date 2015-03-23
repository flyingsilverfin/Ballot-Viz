function loaded() {
	var im = document.getElementById("svg_image");
	var container = document.getElementById("svg_container");
	im.width = container.clientWidth;
}

function loadSVG(location) {
	var im = document.getElementById("svg_image");
	//adding some sort of timestamp forces browser to redraw image, otherwise wouldn't show up half the time
	im.data = BASE_URL + instanceDirectory + "/res/" + location + "?timestamp" + Date.now();
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

function showTooltip(elem, occupant, contractType, rent, roomType) {
	console.log("showing tooltip");
	var im = document.getElementById("svg_image");
	var imLeft = im.getBoundingClientRect().left;
	var imTop = im.getBoundingClientRect().top - 150;
	var elemPos = elem.target.getBoundingClientRect();
	//var posLeft = (imLeft + elemPos.left  + 50) + "px"; //THIS NEEDS TO BE FIXED NEXT!!!
	var posTop = (imTop + elemPos.top - 50) + "px";
	var posLeft = (elemPos.left + 50) + "px"; //TODO: replace the hardcoded 50 addition
	//var posTop = (elemPos.top - 50) + "px";
	console.log(elemPos);
	
	document.getElementById("occupant").innerHTML = occupant;
	document.getElementById("contract_type").innerHTML = contractType;
	rent = document.getElementById("rent").innerHTML = rent;
	roomType = document.getElementById("room_type").innerHTML = roomType;
	var toolTip = document.getElementById("tooltip");
	toolTip.style.left = posLeft;
	toolTip.style.top = posTop;
	toolTip.style.display = "inline";
}

function hideTooltip() {
	console.log("hiding tooltip");
	var tooltip = document.getElementById("tooltip");
	tooltip.style.display = "none";
}

/*
function rotateCW() {

}

function rotateCCW() {

}*/