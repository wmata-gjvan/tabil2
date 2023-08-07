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
    var request = "./createConfigFile?station={0}&buffertime={1}&arrcount={2}&pltcount={3}&weekdaystart1={4}&weekdayend1={5}&weekdaystart2={6}&weekdayend2={7}&weekendstart1={8}&weekendend1={9}&weekendstart2={10}&weekendend2={11}";
    var station=document.getElementById("stationID").value;
    var bufferTime=document.getElementById("bufferTime").value;
    var arrCount=document.getElementById("arrCountdown").value;
    var pltCount=document.getElementById("platformCountdown").value;

    var weekdaystart1=document.getElementById("weekdaystart1").value;
    var weekdayend1=document.getElementById("weekdayend1").value;
    var weekdaystart2=document.getElementById("weekdaystart2").value;
    var weekdayend2=document.getElementById("weekdayend2").value;

    var weekendstart1=document.getElementById("weekendstart1").value;
    var weekendend1=document.getElementById("weekendend1").value;
    var weekendstart2=document.getElementById("weekendstart2").value;
    var weekendend2=document.getElementById("weekendend2").value;
 
    
    request = request.replace("{0}", station).replace("{1}", bufferTime).replace("{2}", arrCount).replace("{3}", pltCount).replace("{4}", weekdaystart1).replace("{5}", weekdayend1).replace("{6}", weekdaystart2).replace("{7}", weekdayend2).replace("{8}", weekendstart1 ).replace("{9}", weekendend1 ).replace("{10}", weekendstart2 ).replace("{11}", weekendend2 )
    
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