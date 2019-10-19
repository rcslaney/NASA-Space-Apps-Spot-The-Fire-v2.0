from flask import Flask, request, send_from_directory
import requests
import csv
import json

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')


@app.route('/html/<path:path>')
def send_js(path):
    return send_from_directory('html', path)


@app.route("/api/fire_data")
def send_fire_data():
    server_request = requests.get("https://firms.modaps.eosdis.nasa.gov/active_fire/c6/text/MODIS_C6_South_America_24h.csv")
    response = server_request.content.decode("UTF8")
    result = []
    skip = True
    for row in csv.reader(response.splitlines(), delimiter=','):
        if skip:
            skip = False
            continue
        result.append([row[0], row[1], int(row[8])/100])
    return json.dumps(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)