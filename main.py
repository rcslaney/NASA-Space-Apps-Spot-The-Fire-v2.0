from flask import Flask, request, send_from_directory, Response, abort, send_file
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
from PIL import Image, ExifTags

if os.environ.get('RUNNING_LOCALLY') is not None:
    UPLOAD_FOLDER = "uploads/"
else:
    UPLOAD_FOLDER = '/tmp/'


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.register_blueprint(api)


@app.route('/app/')
def send_homepage():
    return send_file('html/test/index.html')


@app.route('/app/<path:path>')
def send_html(path):
    return send_from_directory('html/test', path)


@app.route('/uploads/<path:path>')
def send_upload(path):
    return send_from_directory(UPLOAD_FOLDER, path)


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


def convert_to_binary_data(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binary_data = file.read()
    return binary_data


@app.route('/uploadreport', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return "No file submitted."
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return 'No selected file'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.split(".")[len(filename.split(".")) - 1]
            saving_filename = x = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16)) + "." + ext
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], saving_filename)
            file.save(filepath)

            image = Image.open(filepath)
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = dict(image.getexif().items())

            if orientation in exif:
                if exif[orientation] == 3:
                    image = image.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    image = image.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    image = image.rotate(90, expand=True)
                image.save(filepath)

            image.close()

            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor()

            query = "INSERT INTO images (mimetype, imageblob) VALUES (%s, %s)"

            try:
                cursor.execute(query, [file.mimetype, convert_to_binary_data(filepath)])
                cnx.commit()
            except Exception as e:
                return json.dumps({"status": 'error', 'status_extended': 'Failed to submit the insert query: ' + repr(e)})

            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], saving_filename))

            query = ("INSERT INTO reports (lat,lng,text,imgid,score,userid,reporttype) "
                     "VALUES (%s,%s,%s,%s,%s,%s,%s) ")

            # Do the query
            try:
                cursor.execute(query, [request.form["lat"], request.form["lng"], request.form["reportdescription"], cursor.lastrowid, 0, 1, "fire"])
                cnx.commit()
            except Exception as e:
                return json.dumps({"status": 'error', 'status_extended': 'Failed to submit the insert query: ' + repr(e)})


            # Close connection
            cursor.close()
            cnx.close()
    return "Finished."


@app.route("/uploaded_image")
def show_image():
    # Connect to SQL Server
    cnx = None
    try:
        cnx = connect()
    except sql.Error as e:
        return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

    cursor = cnx.cursor(dictionary=True)

    query = "SELECT * FROM images WHERE id = %s"

    try:
        cursor.execute(query, [request.args["id"]])
    except Exception as e:
        return json.dumps({"status": 'error', 'status_extended': 'Failed to find image: ' + repr(e)})

    ret_val = cursor.fetchall()

    if cursor.rowcount != 1:
        abort(404)

    return Response(ret_val[0]["imageblob"], mimetype=ret_val[0]["mimetype"])


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
