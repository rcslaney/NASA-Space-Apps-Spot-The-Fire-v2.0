function buttonClick(e) {
    bg = e.parentElement;
    console.log(bg)
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
    document.getElementById("scrollable_bubble").innerHTML = html;
}

function close_popup() {
    openPopup("NEWS", "4:20pm", "")
    document.getElementById("bubble").style.height = "";
}

function message_html(name, last_message, time, img_path) {
    return "<span class='message'><img src='" + img_path + "'><h3>" + name + "</h3><h3 class='title2'>" + time + "</h3><br><p>" + last_message + "</p><br></span>"
}

function report() {
    openPopup("Send report", "Reporting", "<form><input id=\"fireimage\" name=\"fireimage\" type=\"file\" accept=\"image/*;capture=camera\" style='opacity: 0; position: absolute; width: 0.1px'><label for='fireimage' id='uploadfile'>Upload image</label><span id='fireimagetext'></span></form>")
    document.getElementById("fireimage").addEventListener("change", function (e) {
        document.getElementById("fireimagetext").innerHTML = "File: " + e.target.files[0]["name"];
    })
}

function openPopupPage(title, title2, pagepath) {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            // Typical action to be performed when the document is ready:

            history.pushState({
                "name": title,
                "prevPage": {"html": xhttp.responseText, "title": title, "title2": title2}
            }, null, "#" + title)

            openPopup(title, title2, xhttp.responseText);
        }
    };
    xhttp.open("GET", pagepath, true);
    xhttp.send();
}

history.replaceState({"name": "home"}, null, "#home")

window.onpopstate = function (event) {
    console.log(event.state);
    if (event.state["name"] === "home") {
        close_popup()
    } else if (event.state["prevPage"] !== undefined) {
        data = event.state["prevPage"];
        openPopup(data["title"], data["title2"], data["html"])
    }
};

function populateFormPositionGPS(position) {
    console.log(position)
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

function addMarkers() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log("Successfully loaded markers", xhttp.responseText);
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
                    content: "<img src='/" + mdata["imgpath"] + "'><p>Location: " + mdata["lat"] + ", " + mdata["lng"] + "</p><p>Report type: " + mdata["reporttype"] + "</p><p>" + mdata["text"] + "</p>"
                });

                // Attach it to the marker we've just added
                google.maps.event.addListener(marker, 'click', infoCallback(infowindow, marker));
            }
        }
    };

    xhttp.open("GET", "/api/previews?lat=0&lng=0&r=200");

    xhttp.send()
}

function showMessages() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log("Successfully loaded messages", xhttp.responseText);
            data = JSON.parse(xhttp.responseText);
            conversations = data["return"];
            messages_html = "<span class='new_message' onclick='sendMessageDialogue()'>+ Create new message</span>";
            for (i in conversations) {
                cdata = conversations[i];
                console.log(cdata)
                messages_html += message_html(cdata["name"], cdata["message"], cdata["timestamp"].split(" ")[1], cdata["otheruserpic"])
            }

            openPopup("Direct messages", "Richard Slaney", messages_html)
            history.pushState({"name": "messages", "data": messages_html}, null, "#messages")
        }
    };

    xhttp.open("GET", "/api/preview?userid=1");

    xhttp.send()
}

function sendMessageDialogue() {
    var xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log("Successfully loaded messages", xhttp.responseText);
            data = JSON.parse(xhttp.responseText);
            users = data["return"];
            select_html = "";
            for (i in users) {
                user = users[i];
                select_html += "<option value='" + user["id"] + "'>" + user["name"] + "</option>";
            }

            openPopupPage("Send a message", "Messaging", "pages/send_message.html")
            document.getElementById("recepient").innerHTML = select_html;
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

    xhttp.open("GET", "/api/send_message?userfromid=1&usertoid=" + document.getElementById("recepient").value + "&message=" + document.getElementById("message").value);

    xhttp.send()
}