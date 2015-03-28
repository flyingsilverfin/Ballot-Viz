var currentlySelected = "bbc_a";
//the following object translates between the site button's ID and that site's URI
var siteFilenames = {
	"bbc_a" : 'bbc-a-floor-combined.svg',
	"bbc_b" : 'bbc-b-floor-combined.svg'
}

/*
	Ok i'm going to start building it toward controlling my own caching...
	keep track of etags with this object
*/

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
	
	setInterval(update, 5000);	
}

//thanks to http://stackoverflow.com/questions/247483/http-get-request-in-javascript
var HttpClient = function() {
    this.get = function(aUrl, aCallback) {
        var anHttpRequest = new XMLHttpRequest();
        anHttpRequest.onreadystatechange = function() { 
            if (anHttpRequest.readyState == 4 && anHttpRequest.status == 200)
                aCallback(anHttpRequest.responseText);
        }

        anHttpRequest.open( "GET", aUrl, true );            
        anHttpRequest.send( null );
    }
}

//call the callback if the url has changed (200 OK received not 304 no change)
function ifSiteChanged(site, callback, callbackParams) {
	var httpRequest = new XMLHttpRequest();
	var priorEtag = siteEtags[site];
	httpRequest.onreadystatechange = function() {
		var newEtag = httpRequest.getResponseHeader("etag");
		if (newEtag != priorEtag && newEtag != null) {
			console.log("Different etags, before: " + priorEtag + ", after: " + newEtag);
			siteEtags[site] = newEtag;
			//WARNING: THIS IS ***SHIT*** CODE
			//RIGHT NOW WE CAN ALSO HAVE A PROBLEM IF THE FILE IS UPDATED WHILE WE ARE CHECKING THE ETAG BUT IT WON'T WRITE THE EVEN NEWER ETAG...
			callback.apply(undefined, callbackParams); //undefined needs ot here for some reason
		}
	}
	httpRequest.open("GET", "res/" + siteFilenames[site], true);
	httpRequest.send(null);	
}

function update() {
	/*
		This is inefficient because:
			If there's a change made, we do two GET requests to the same file
		However I think that since most of the time there won't be a change made, this is worth it
	*/
	//pass in URL to test for change, callback function, and callback function parameters
	ifSiteChanged(currentlySelected, loadSVG, [currentlySelected]);
}

function loadSVG(siteName) {
	var im = embedded.getElementById("svg_image");
	//adding some sort of timestamp forces browser to redraw image, otherwise wouldn't show up half the time (interesting)
	im.data = "res/" + siteFilenames[siteName] + "?time=" + Date.now(); //CANNOT HAVE A PRECEDING SLASH (think regular unix)
	
	document.getElementById(currentlySelected).style.background = "#E0E0E0";
	currentlySelected = siteName;
	var selector = document.getElementById(currentlySelected);
	selector.style.backgroundColor = "white";
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

function showTooltip(elem, room, occupant, camCrsid, contractType, rent, roomType) {
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
	//I'm not quite sure why these values are as they are right, now especially the 2* and why the +25 needs to be there
	//all made sense before having to use embedded iframe... :(
	var posLeft = (imLeft + elemPos.left + elemPos.width/2 - tooltip.getBoundingClientRect().width/2) + "px";
	var posTop = (imTop + elemPos.top + headerHeight - 2*tooltip.getBoundingClientRect().height + 25) + "px";

	//var posLeft = (imLeft + elemPos.left - sidebarWidth  + elemPos.width/2 - tooltip.getBoundingClientRect().width/2) + "px";
	//var posTop = (imTop + elemPos.top - headerHeight - tooltip.getBoundingClientRect().height - 10) + "px";
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
