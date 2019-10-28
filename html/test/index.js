function buttonClick(e) {
    bg = e.parentElement;
    sbs = bg.children[0].children;
    if (sbs[0].style.bottom === "") {
        for (key in sbs) {
            sbs[key].style.bottom = "20px";
        }
    } else {
        for (key in sbs) {
            sbs[key].style.bottom = "";
        }
    }
}

function openPopup(title, title2, html) {
    document.getElementById("title").innerHTML = title;
    document.getElementById("title2").innerHTML = title2;
    document.getElementById("bubble").style.height = "calc(100vh - 40px)";
    document.getElementById("scrollable_bubble").style.padding = "";
    document.getElementById("scrollable_bubble").innerHTML = html;
    document.getElementById("dimmed").style.pointerEvents = "initial";
    document.getElementById("dimmed").style.background = "rgba(0, 0, 0, 0.3)";
    document.getElementById("dimmed").style.cursor = "pointer";
}

function close_popup() {
    showNews()
    document.getElementById("bubble").style.height = "";
    document.getElementById("dimmed").style.pointerEvents = "none";
    document.getElementById("dimmed").style.background = "rgba(0, 0, 0, 0)";
    document.getElementById("dimmed").style.cursor = "";
    addAreas();
    addPOIMarkers();
    addReportMarkers();
}

function message_html(id, name, last_message, time, imgid) {
    return "<span class='message' onclick='viewConversation(" + id + ")'><img src='/uploaded_image?id=" + imgid + "'><h3>" + name + "</h3><h3 class='title2'>" + time + "</h3><br><p>" + last_message + "</p><br></span>"
}

function report() {
    openPopup("Send report", "Reporting", "<form><input id=\"fireimage\" name=\"fireimage\" type=\"file\" accept=\"image/*;capture=camera\" style='opacity: 0; position: absolute; width: 0.1px'><label for='fireimage' id='uploadfile'>Upload image</label><span id='fireimagetext'></span></form>")
    document.getElementById("fireimage").addEventListener("change", function (e) {
        document.getElementById("fireimagetext").innerHTML = "File: " + e.target.files[0]["name"];
    })
}

function openPopupPage(title, title2, pagepath, callback = function () {
}) {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            // Typical action to be performed when the document is ready:

            history.pushState({
                "name": title,
                "prevPage": {"html": xhttp.responseText, "title": title, "title2": title2}
            }, null, "#" + title)

            openPopup(title, title2, xhttp.responseText);
            callback()
        }
    };
    xhttp.open("GET", pagepath, true);
    xhttp.send();
}

history.replaceState({"name": "home"}, null, "#home")

window.onpopstate = function (event) {
    if (event.state["name"] === "home") {
        close_popup()
    } else if (event.state["prevPage"] !== undefined) {
        data = event.state["prevPage"];
        openPopup(data["title"], data["title2"], data["html"])
    }
};

function populateFormPositionGPS(position) {
    document.getElementById("lat").value = position.coords.latitude;
    document.getElementById("lng").value = position.coords.longitude;
}

function populateFormPositionMap() {
    position = map.getCenter();
    document.getElementById("lat").value = position.lat();
    document.getElementById("lng").value = position.lng();
}

function submitReport() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            openPopup("Report uploaded!", "Reporting", "<p>Your report has been uploaded, thank you for your help.</p>");
        }
    };
    xhr.open('POST', '/uploadreport', true);
    var formData = new FormData();
    formData.append("id", getID())
    formData.append("file", document.getElementById("fireimage").files[0]);
    formData.append("lat", document.getElementById("lat").value);
    formData.append("lng", document.getElementById("lng").value);
    formData.append("reportdescription", document.getElementById("reportdescription").value);
    xhr.send(formData); // Simple!
}

function infoCallback(infowindow, marker) {
    return function () {
        infowindow.open(map, marker);
    };
}

function addReportMarkers() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            data = JSON.parse(xhttp.responseText);
            reports = data["return"];
            for (i = 0; i < reports.length; i++) {
                mdata = reports[i];

                // First marker
                var marker = new google.maps.Marker({
                    position: new google.maps.LatLng(mdata["lat"], mdata["lng"]),
                    map: map,
                    title: mdata["title"]
                });

                // First infowindow
                var infowindow = new google.maps.InfoWindow({
                    content: "<img src='/uploaded_image?id=" + mdata["imgid"] + "' style='width: 200px;'><p>Location: " + mdata["lat"] + ", " + mdata["lng"] + "</p><p>Report type: " + mdata["reporttype"] + "</p><p>" + mdata["text"] + "</p>"
                });

                // Attach it to the marker we've just added
                google.maps.event.addListener(marker, 'click', infoCallback(infowindow, marker));
            }
        }
    };

    xhttp.open("GET", "/api/reports?lat=0&lng=0&r=200");

    xhttp.send()
}


function addPOIMarkers() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            data = JSON.parse(xhttp.responseText);
            reports = data["return"];
            for (i = 0; i < reports.length; i++) {
                mdata = reports[i];

                // First marker
                var marker = new google.maps.Marker({
                    position: new google.maps.LatLng(mdata["lat"], mdata["lng"]),
                    map: map,
                    title: mdata["title"]
                });

                // First infowindow
                var infowindow = new google.maps.InfoWindow({
                    content: "<p>Location: " + mdata["lat"] + ", " + mdata["lng"] + " " + Math.round(mdata["dst"]) + "km away</p><p>Title: " + mdata["title"] + "</p><p>" + mdata["description"] + "</p>"
                });

                // Attach it to the marker we've just added
                google.maps.event.addListener(marker, 'click', infoCallback(infowindow, marker));
            }
        }
    };

    xhttp.open("GET", "/api/poi?lat=0&lng=0&r=200");

    xhttp.send()
}

function showMessages() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            data = JSON.parse(xhttp.responseText);
            conversations = data["return"];
            messages_html = "<span class='new_message' onclick='sendMessageDialogue()'>+ Create new message</span>";
            for (i in conversations) {
                cdata = conversations[i];
                messages_html += message_html(i, cdata["name"], cdata["message"], cdata["timestamp"].split(" ")[1], cdata["otheruserpicid"])
            }

            openPopup("Direct messages", userdata["firstname"] + " " + userdata["lastname"], messages_html)
            history.pushState({
                "name": "messages",
                "prevPage": {"title": "Direct messages", "title2": userdata["firstname"] + " " + userdata["lastname"], "html": messages_html}
            }, null, "#messages")
        }
    };

    xhttp.open("GET", "/api/preview?userid=" + getID());

    xhttp.send()
}

function sendMessageDialogue() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            data = JSON.parse(xhttp.responseText);
            users = data["return"];
            select_html = "";
            for (i in users) {
                user = users[i];
                select_html += "<option value='" + user["id"] + "'>" + user["name"] + "</option>";
            }

            openPopupPage("Send a message", "Messaging", "pages/send_message.html", function () {
                document.getElementById("recepient").innerHTML = select_html;
            })
        }
    };

    xhttp.open("GET", "/api/users");

    xhttp.send()
}

function sendMessage() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            showMessages()
        }
    };

    xhttp.open("GET", "/api/send_message?userfromid=" + getID() + "&usertoid=" + document.getElementById("recepient").value + "&message=" + document.getElementById("message").value);

    xhttp.send()
}

function viewConversation(userid) {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            data = JSON.parse(xhttp.responseText);
            messages = data["return"];
            messages_html = "";
            for (i in messages) {
                message = messages[i];
                if (message["usertoid"] == userid) {
                    messages_html += "<span class='message_bubble_outer'><span class='message_bubble'>" + message["message"] + "</span></span>";
                } else {
                    messages_html += "<span class='message_bubble_outer'><span class='message_bubble reply'>" + message["message"] + "</span></span>";
                }
            }

            messages_html += "<span class='message_bubble_outer reply_field'><input type='text' placeholder='Reply' id='message'><input type='hidden' id='recepient' value='" + userid + "'><button type='button' onclick='sendMessage()'>Send</button></span>";

            history.pushState({
                "prevPage": {
                    "title": "Conversation",
                    "title2": "",
                    "html": messages_html
                }
            }, null, "#conversation" + userid);
            openPopup("Conversation", "", messages_html)
        }
    };

    xhttp.open("GET", "/api/messages?userid=" + getID() + "&userid2=" + userid);

    xhttp.send()
}

function addAreas() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            data = JSON.parse(xhttp.responseText);
            zones = data["return"];
            for (i in zones) {
                zone = zones[i];
                coords = zone.wkt.coordinates[0][0]

                gcoords = [];

                for (i in coords) {
                    gcoords[i] = {lat: coords[i][0], lng: coords[i][1]}
                }

                // Construct the polygon.
                var poly = new google.maps.Polygon({
                    paths: gcoords,
                    strokeColor: '#FF0000',
                    strokeOpacity: 0.8,
                    strokeWeight: 2,
                    fillColor: '#FF0000',
                    fillOpacity: 0.35
                });
                poly.setMap(map)
            }
            // history.pushState({"prevPage": {"title": "Conversation", "title2": "", "html": messages_html}}, null, "#conversation" + userid);
            // openPopup("Conversation", "", messages_html)
        }
    };

    xhttp.open("GET", "/api/zones?lat=0&lng=0&r=200");

    xhttp.send()
}

function showHelp() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            data = JSON.parse(xhttp.responseText);
            helps = data["return"];
            help_html = "<span class='new_message' onclick='requestHelp()'>Request help</span>";
            for (i in helps) {
                hdata = helps[i];
                help_html += "<span class='help_box'><img src='/uploaded_image?id=" + hdata["imgid"] + "'><h3>" + hdata["title"] + "</h3><h4>" + hdata["fullname"] + "</h4></span>"
            }

            openPopup("Help requests", userdata["firstname"] + " " + userdata["lastname"], help_html)
            history.pushState({
                "name": "messages",
                "prevPage": {"title": "Help requests", "title2": userdata["firstname"] + " " + userdata["lastname"], "html": help_html}
            }, null, "#helprequests")
        }
    };

    xhttp.open("GET", "/api/help?lat=0&lng=0&r=200");

    xhttp.send()
}

function requestHelp() {
    openPopupPage("Request help", userdata["firstname"] + " " + userdata["lastname"], "pages/request_help.html")
}

function showLogin() {
    openPopupPage("Login", "My account", "pages/login.html")
}

function submitLogin() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            data = JSON.parse(xhr.responseText)
            if (data["status"] === "success") {
                openPopup("Logged in!", "Success", "<p>You have been logged in successfully.</p>");
                document.cookie = 'session=' + data["session"] + '; expires=Mon, 3 Aug 2020 20:47:11 UTC; path=/'
            } else {
                document.getElementById("status_login").innerHTML = data["status_extended"]
            }
        }
    };
    xhr.open('POST', '/api/login', true);
    var formData = new FormData();
    formData.append("email", document.getElementById("email").value);
    formData.append("password", document.getElementById("password").value);
    xhr.send(formData); // Simple!
}

userdata = {
    "firstname": "Anonymous",
    "lastname": ""
};

function getID() {
    var xhttp = new XMLHttpRequest();
    xhttp.open("GET", "/api/getuser", false);
    xhttp.send()
    data = JSON.parse(xhttp.responseText);
    if (data["status"] === "success") {
        userdata = data["alldata"];
        return data["userid"];
    } else {
        return 0
    }
}

function showPoi() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            data = JSON.parse(xhttp.responseText);
            pois = data["return"];
            // id, lat, lng, title, description, userid, dst
            poi_html = "";
            for (i in pois) {
                hdata = pois[i];
                poi_html += "<span class='poi_box' onclick='map.panTo(new google.maps.LatLng(" + hdata['lat'] + "," + hdata['lng'] + ")); close_popup()'><h3>" + hdata["title"] + "</h3><h3 class='dist'>" + Math.round(hdata['dst'] * 10) / 10 + " km away</h3><br><p>" + hdata["description"] + "</p></span>"
            }

            openPopup("Points of interest", userdata["firstname"] + " " + userdata["lastname"], poi_html)
            history.pushState({
                "name": "messages",
                "prevPage": {"title": "Poi requests", "title2": userdata["firstname"] + " " + userdata["lastname"], "html": poi_html}
            }, null, "#poirequests")
        }
    };

    xhttp.open("GET", "/api/poi?lat=0&lng=0&r=200");

    xhttp.send()
}

function showRoutes() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            data = JSON.parse(xhttp.responseText);
            routes = data["return"];
            // line, reputation, title, description, timestamp
            for (i in routes) {
                hdata = routes[i];
                map = document.getElementById("googleMap")
                poly = new google.maps.Polyline({
                    strokeColor: '#FF0000',
                    strokeOpacity: 1.0,
                    strokeWeight: 2.5 + (reputation / 100),
                    map: map,
                    path: google.maps.geometry.encoding.decodePath(hdata["line"])
                });
            }

            openPopup("Help requests", userdata["firstname"] + " " + userdata["lastname"], route_html)
            history.pushState({
                "name": "messages",
                "prevPage": {"title": "Route requests", "title2": userdata["firstname"] + " " + userdata["lastname"], "html": route_html}
            }, null, "#routerequests")
        }
    };
}

function readURL(input) {
    if (input.files && input.files[0]) {
        loadImage(
            input.files[0],
            function (img) {
                document.getElementById("imgpreview").innerHTML = "";
                document.getElementById("imgpreview").appendChild(img);
            }
        );
    }
}

function ellipsizeTextBox(id) {
    var el = document.getElementById(id);
    var wordArray = el.innerHTML.split(' ');
    while(el.scrollHeight > el.offsetHeight) {
        wordArray.pop();
        el.innerHTML = wordArray.join(' ') + '...';
     }
}

function showNews() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            data = JSON.parse(xhttp.responseText);
            news = data["return"];

            document.getElementById("scrollable_bubble").innerHTML = "<b>" + news[0]["title"] + ": </b> " + news[0]["contents"]
            document.getElementById("scrollable_bubble").style.padding = "0 13px";
            document.getElementById("title2").innerText = news[0]["timestamp"].split(" ")[1];

            ellipsizeTextBox("scrollable_bubble")
        }
    };

    xhttp.open("GET", "/api/news?lat=0&lng=0&r=200");

    xhttp.send()
}

