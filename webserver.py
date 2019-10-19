from flask import Flask, request, send_from_directory, flash, redirect, url_for
from werkzeug.utils import secure_filename
import requests
import csv
import json
import os
import random
import string

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/html/<path:path>')
def send_html(path):
    return send_from_directory('html', path)


@app.route('/uploads/<path:path>')
def send_upload(path):
    return send_from_directory('uploads', path)


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
    return json.dumps({"result": result, "status": "success", "status_extended": ""})


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.split(".")[len(filename.split(".")) - 1]
            saving_filename = x = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16)) + "." + ext
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], saving_filename))
            return redirect(os.path.join(app.config['UPLOAD_FOLDER'], saving_filename))
    return '''
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form method=post enctype=multipart/form-data>
          <input type=file name=file>
          <input type=submit value=Upload>
        </form>
        '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
