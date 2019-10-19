import datetime

from flask import Flask, request, send_from_directory
import requests
import csv
import json
import mysql.connector as sql
import geopy
from geomet import wkt

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')


def connect():
    return sql.connect(user='root', password='BananaShoestring490', host='35.189.219.41', database='app')


@app.route('/api/poi')
def get_poi():
    # x,y is center of screen
    args = request.args
    if (len(args) != 3):
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
    else:
        if ('lat' not in args.keys or ('lng' not in args.keys) or ('r' not in args.keys)):
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
        else:
            lat = args['lat']
            lng = args['lng']
            r = args['r']
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor(dictionary=True)
            query = ("SELECT id, lat, lng, title, description, userid "
                     "FROM poi "
                     "WHERE ABS(lat-%s) <= %s AND ABS(lng-%s)<=%s "
                     "ORDER BY POWER(lat-%s, 2) + POWER(lng-%s, 2) ASC")
            # Do the query
            cursor.execute(query, [lat, r, lng, r, lat, lng])
            ret_val = cursor.fetchall()
            for index, (_, poi_lat, poi_lng, _, _, _) in enumerate(ret_val):
                ret_val[index]['dst'] = geopy.distance.distance((poi_lat, poi_lng), (lat, lng))
            cursor.close()
            cnx.close()
            return json.dumps({"status": 'success', 'status_extended': '', 'return': ret_val})


@app.route('/api/reports')
def get_reports():
    # x,y is center of screen
    args = request.args
    if len(args) != 3:
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
    else:
        if 'lat' not in args.keys or ('lng' not in args.keys) or ('r' not in args.keys):
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
        else:
            lat = args['lat']
            lng = args['lng']
            r = args['r']
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor(dictionary=True)
            query = ("SELECT id, lat, lng, text, imgpath, score, userid, reporttype, timestamp "
                     "FROM reports "
                     "WHERE ABS(lat-%s) <= %s AND ABS(lng-%s)<=%s "
                     "ORDER BY POWER(lat-%s, 2) + POWER(lng-%s, 2) ASC")
            # Do the query
            cursor.execute(query, [lat, r, lng, r, lat, lng])
            ret_val = cursor.fetchall()
            # Add distance from query point to return
            for index, (poi_lat, poi_lng, _, _, _, _, _, _) in enumerate(ret_val):
                ret_val[index]['dst'] = geopy.distance.distance((poi_lat, poi_lng), (lat, lng))
            cursor.close()
            cnx.close()
            return json.dumps({"status": 'success', 'status_extended': '', 'return': ret_val})


@app.route('/api/messages')
def get_preview():
    args = request.args
    if len(args) != 1:
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 1 arguments: userid'})
    else:
        if 'userid' not in args.keys():
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 1 arguments: userid'})
        else:
            userid = args['userid']
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor(dictionary=True)
            query = ("SELECT id,userfromid,usertoid,message, timestamp "
                     "FROM messages "
                     "WHERE userfromid = %s OR usertoid = %s ")

            # Do the query
            cursor.execute(query, (int(userid), int(userid)))
            ret_val = cursor.fetchall()
            # Add distance from query point to return
            latest = {}
            print(repr(ret_val))
            for index, row in enumerate(ret_val):
                dict_insert = {'id': row["id"], 'message': row["message"], 'timestamp': row["timestamp"]}
                otheruser = None
                if row["userfromid"] == int(userid):
                    otheruser = row["usertoid"]
                else:
                    otheruser = row["userfromid"]
                if otheruser in latest.keys():
                    if row["timestamp"] >= latest[otheruser]["timestamp"]:
                        latest[otheruser] = dict_insert
                else:
                    latest[otheruser] = dict_insert
            cursor.close()
            cnx.close()
            for otherid in latest.keys():
                latest[otherid]["timestamp"] = datetime.datetime.strftime(latest[otheruser]["timestamp"], '%Y-%m-%d %H:%M:%S')
            # del(latest[int(userid)])
            return json.dumps({"status": 'success', 'status_extended': '', 'return': latest})


@app.route('/api/news')
def get_news():
    # x,y is center of screen
    args = request.args

    if (len(args) != 3):
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
    else:
        if ('lat' not in args.keys or ('lng' not in args.keys) or ('r' not in args.keys)):
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
        else:
            lat = args['lat']
            lng = args['lng']
            r = args['r']
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor()
            query = ("SELECT id, title, contents, severity, timestamp, lat, lng, radius"
                     "FROM news "
                     "WHERE ABS(lat-%s) <= %s AND ABS(lng-%s)<=%s "
                     "ORDER BY timestamp")

            # Do the query
            cursor.execute(query, [lat, r, lng, r, lat, lng])
            ret_val = cursor.fetchall()

            # Close connection
            cursor.close()
            cnx.close()

            return json.dumps({"status": 'success', 'status_extended': '', 'return': ret_val})


@app.route('/api/send_message')
def send_message():
    args = request.args

    if (len(args) != 3):
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: userfromid, usertoid, message'})
    else:
        if ('userfromid' not in args.keys or ('usertoid' not in args.keys) or ('message' not in args.keys)):
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: userfromid, usertoid, message'})
        else:
            userfromid = args['userfromid']
            usertoid = args['usertoid']
            message = args['message']
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor()
            query = ("INSERT INTO messages (userfromid, usertoid, message) "
                     "VALUES (%s, %s,%s)")

            # Do the query
            cursor.execute(query, [userfromid, usertoid, message])
            ret_val = cursor.fetchall()

            # Close connection
            cursor.close()
            cnx.close()
            return json.dumps({"status": 'success', 'status_extended': '', 'return': ret_val})

@ app.route('/api/send_poi')
def send_poi():
    args = request.args
    real_args = ["lat", "lng", "title", "description", "userid"]
    if (len(args) != 3):
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 5 arguments: lat, lng, title, description, userid'})
    else:
        if (set(real_args) != set(args)):
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 5 arguments: lat, lng, title, description, userid'})
        else:
            lat = args['lat']
            lng = args['lng']
            title = args['title']
            description = args['description']
            userid = args['userid']
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor()
            query = ("INSERT INTO poi (lat,lng,title,description,userid) "
                     "VALUES (%s,%s,%s,%s,%s) ")

            # Do the query
            cursor.execute(query, [lat, lng, title, description, userid])
            ret_val = cursor.fetchall()

            # Close connection
            cursor.close()
            cnx.close()
            return json.dumps({"status": 'success', 'status_extended': '', 'return': ret_val})


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
        result.append([row[0], row[1], int(row[8]) / 100])
    return json.dumps(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
