function loaded() {
	var im = document.getElementById("svg_image");
	var container = document.getElementById("svg_container");
	im.width = container.clientWidth;
}

function loadSVG(location) {
	var im = document.getElementById("svg_image");
	
	im.data = BASE_URL + instanceDirectory + "/res/" + location;
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

/*
function rotateCW() {

}

function rotateCCW() {

}*/