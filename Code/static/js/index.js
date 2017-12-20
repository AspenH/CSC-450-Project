//=====================Global Vars==================================
var webSocket = null;
var image = null;
var acusArray;

function slateViewModel() {
    image = ko.observable("");

    var address = "ws://127.0.0.1:8090/ws";

    if ("WebSocket" in window) {
        webSocket = new WebSocket(address);
    } else if ("MozWebSocket" in window) {
        webSocket = new MozWebSocket(address);
    }

    webSocket.onopen = function() {
        if (window.location.pathname == "/index.html" ||
            window.location.pathname == "/") {
            webSocket.send('register');
        } else if (window.location.pathname == "/detect.html") {
            webSocket.send('detect');
        }
    }

    webSocket.onclose = function(e) {
        // webSocket = null;
        webSocket.send('disconnect');
    }

    webSocket.onmessage = function(e) {
        if (e.data.startsWith("cvoMessage")) {

            acusArray = e.data.split('|');

            if (acusArray.length > 2) {
                for (var i = 1; i < acusArray.length; i++) {
                    acusArray[i] = acusArray[i].split(',');
                }
                for (var i = 0; i < acusArray[1].length; i++) {
                    jQuery('<option/>', {
                        value: i,
                        html: acusArray[1][i]
                    }).appendTo('#users');
                }
                for (var i = 0; i < 6; i++) {
                    jQuery('<option/>', {
                        value: i,
                        html: i
                    }).appendTo('#fingers');
                }
                for (var i = 0; i < acusArray[2].length; i++) {
                    jQuery('<option/>', {
                        value: acusArray[2][i],
                        html: acusArray[2][i]
                    }).appendTo('#states');
                }
            }

            document.getElementById("registration").style.display = "block";
            document.getElementById("connection").style.display = "none";

        } else if (e.data != "Dropped Frame") {
            image('data:image/jpeg;base64,' + e.data);
        }
    }

}

function sendCompesInfo() {
    var id = document.getElementById('POST');
    var masterString = "sendCompes";
    for (var i = 0; i < id.elements.length; i++) {
        masterString += "|" + id.elements[i].value;
    }
    webSocket.send(masterString);
}

function sendAssignInfo() {
    var msg = "assign|";
    msg += $("#users option:selected").text() + "|";
    msg += $("#fingers option:selected").text() + "|";
    msg += $("#states option:selected").text();
    webSocket.send(msg);
}

$(document).ready(function() {
    /*
    Description: This function specifies the behaviour of the program when the user starts the application.
    Inputs: an event related to the application opening
    Outputs: N\A
    Notes: This program sets up the knockout bindings and starts the python subprocess
           that houses the Twisted Client.
    */
    //Apply knockout data-bindings
    ko.applyBindings(new slateViewModel());
});

$(window).on("unload", function() {
    /*
    Author: 
    Description: 
    Input: N/A
    Output: N/A
    Notes: N/A
    */
    webSocket.close();
});