var mainTemplate;
var trainsList;
const req = new XMLHttpRequest();
function onload() {
    req.open("GET", "/getOptions", false);
    req.send()
    var selectList = document.getElementById("stationID")
    var files = JSON.parse(req.response)
    for(let i in files) {
        var option = document.createElement("option");
        option.text = files[i]
        option.id = files[i]
        selectList.add(option)
    }
}

function createFile() {
    var request = "./createConfigFile?station={0}&buffertime={1}&arrcount={2}&pltcount={3}";
    var station=document.getElementById("stationID").value;
    var bufferTime=document.getElementById("bufferTime").value;
    var arrCount=document.getElementById("arrCountdown").value;
    var pltCount=document.getElementById("platformCountdown").value;

    request = request.replace("{0}", station).replace("{1}", bufferTime).replace("{2}", arrCount).replace("{3}", pltCount)
    
    req.open("GET", request, true);
    req.send();
    req.addEventListener("loadend", loadEnd);
    

}

function start() {  
    var request = "./begin";
    req.open("GET", request, false);
    req.send()
    window.close()
}
function loadEnd(e) {
   document.body.innerHTML = '<h2>Config file has been created sucessfully. Click Begin to start using the TABIL</h2><button type="button" onclick="start()">Begin!</button>'
}