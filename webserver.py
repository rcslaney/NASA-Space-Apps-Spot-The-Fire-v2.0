from flask import Flask, request, send_from_directory, flash, redirect, url_for
from werkzeug.utils import secure_filename
import requests
import csv
import json
import os
import random
import string
from api import api
from api import connect
import mysql.connector as sql


UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.register_blueprint(api)

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


@app.route('/uploadreport', methods=['GET', 'POST'])
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
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor()
            query = ("INSERT INTO reports (lat,lng,text,imgpath,score,userid,reporttype) "
                     "VALUES (%s,%s,%s,%s,%s,%s,%s) ")

            # Do the query
            try:
                cursor.execute(query, [request.form["lat"], request.form["lng"], request.form["reportdescription"], os.path.join(app.config['UPLOAD_FOLDER'], saving_filename), 0, 1, "fire"])
                cnx.commit()
            except Exception as e:
                return json.dumps({"status": 'error', 'status_extended': 'Failed to submit the insert query: ' + repr(e)})

            # Close connection
            cursor.close()
            cnx.close()
    return '''
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form method=post enctype=multipart/form-data>
          <input type=file name=file>
          <input type=submit value=Upload>
        </form>
        '''


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
