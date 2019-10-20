import datetime
from polyline.codec import PolylineCodec
from flask import Flask, request, send_from_directory, Blueprint
import requests
import csv
import json
import mysql.connector as sql
import geopy.distance
from geomet import wkt

api = Blueprint('account_api', __name__)


def connect():
    return sql.connect(user='root', password='BananaShoestring490', host='35.189.219.41', database='app')


@api.route('/api/poi')
def get_poi():
    # x,y is center of screen
    args = request.args
    if (len(args) != 3):
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
    else:
        if ('lat' not in args.keys() or ('lng' not in args.keys()) or ('r' not in args.keys())):
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
        else:
            lat = float(args['lat'])
            lng = float(args['lng'])
            r = float(args['r'])
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error:
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor(dictionary=True)
            query = ("SELECT id, lat, lng, title, description, userid "
                     "FROM poi "
                     "WHERE (ABS(lat-%s) <= %s) AND (ABS(lng-%s) <= %s) "
                     "ORDER BY POWER(lat-%s, 2) + POWER(lng-%s, 2) ASC")
            # Do the query
            cursor.execute(query, [lat, r, lng, r, lat, lng])
            ret_val = cursor.fetchall()
            for row in ret_val:
                row["lat"] = float(row['lng'])
                row['lng'] = float(row['lng'])
                row['dst'] = geopy.distance.distance((row['lat'], row['lng']), (lat, lng)).km
            cursor.close()
            cnx.close()
            return json.dumps({"status": 'success', 'status_extended': '', 'return': ret_val})

@api.route('/api/users')
def get_users():
    # Connect to SQL Server
    cnx = None
    try:
        cnx = connect()
    except sql.Error as e:
        print(e)
        return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

    cursor = cnx.cursor(dictionary=True)
    query = ("SELECT id, Concat(firstname, ' ', lastname) as name, profilepicturepath, email, homelat, homelng, reputationscore "
                "FROM users "
                "ORDER BY name DESC")
    # Do the query
    cursor.execute(query)
    ret_val = cursor.fetchall()
    # Add distance from query point to return
    for row in ret_val:
        row["homelat"] = float(row['homelat'])
        row['homelng'] = float(row['homelng'])
    cursor.close()
    cnx.close()
    return json.dumps({"status": 'success', 'status_extended': '', 'return': ret_val})

@api.route('/api/zones')
def get_zones():
    # x,y is center of screen
    args = request.args
    if len(args) != 3:
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
    else:
        if 'lat' not in args.keys() or ('lng' not in args.keys()) or ('r' not in args.keys()):
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
        else:
            lat = float(args['lat'])
            lng = float(args['lng'])
            r = float(args['r'])
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor(dictionary=True)
            query = ("SELECT ST_AsText(zonepoly) as wkt, type, description, timestamp "
                     "FROM zones "
                     "WHERE (ABS(X(Centroid(zonepoly)) - %s) <= %s) AND (ABS(Y(Centroid(zonepoly)) - %s ) <= %s) "
                     "ORDER BY timestamp DESC")
            # Do the query
            cursor.execute(query, [float(lat), float(r), float(lng), float(r)])
            ret_val = cursor.fetchall()
            # Add distance from query point to return
            for val in ret_val:
                val["wkt"] = wkt.loads(val["wkt"])
                val["timestamp"] = datetime.datetime.strftime(val["timestamp"], '%Y-%m-%d %H:%M:%S')
            cursor.close()
            cnx.close()
            return json.dumps({"status": 'success', 'status_extended': '', 'return': ret_val})

@api.route('/api/send_zone')
def send_zone():
    # x,y is center of screen
    args = request.args
    real_args = ['geojson', 'type', 'description']
    if set(args) != set(real_args):
        return json.dumps({'status': 'error', 'status_extended': f'This function takes {len(real_args)} arguments: {real_args}'})
    else:
        data = None
        with open(args['geojson'], 'r') as json_file:
            data = json.load(json_file)
        type = args['type']
        description = args['description']
        # Connect to SQL Server
        cnx = None
        try:
            cnx = connect()
        except sql.Error as e:
            print(e)
            return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

        cursor = cnx.cursor(dictionary=True)
        query = ("INSERT INTO zones (zonepoly,type,description) "
                    "VALUES (ST_GeomFromGeoJSON(%s), %s, %s)")
        # Do the query
        try:
            cursor.execute(query, [data, type,description])
            cnx.commit()
        except:
            return json.dumps({"status": 'error', 'status_extended': 'Failed to submit the insert query'})
        # Close connection
        cursor.close()
        cnx.close()
        return json.dumps({"status": 'success', 'status_extended': ''})


@api.route('/api/routes')
def get_routes():
    # x,y is center of screen
    args = request.args
    if len(args) != 3:
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
    else:
        if 'lat' not in args.keys() or ('lng' not in args.keys()) or ('r' not in args.keys()):
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
        else:
            lat = float(args['lat'])
            lng = float(args['lng'])
            r = float(args['r'])
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor(dictionary=True)

            query = ("SELECT ST_AsText(polyline) as line, reputation, title, description, timestamp "
                     "FROM routes "
                     "WHERE ABS(X(ST_PointN(polyline, ST_NumPoints(polyline)/2)) - %s) <= %s AND ABS(Y(ST_PointN(polyline, ST_NumPoints(polyline)/2)) - %s) <= %s"
                     "ORDER BY timestamp DESC")
            # Do the query
            cursor.execute(query, [float(lat), float(r), float(lng), float(r)])
            ret_val = cursor.fetchall()
            # Add distance from query point to return
            for val in ret_val:
                val["line"] =  PolylineCodec().encode(wkt.loads(val["line"])["coordinates"])
                val["timestamp"] = datetime.datetime.strftime(val["timestamp"], '%Y-%m-%d %H:%M:%S')
            cursor.close()
            cnx.close()
            return json.dumps({"status": 'success', 'status_extended': '', 'return': ret_val})

@api.route('/api/send_route')
def send_route():
    # x,y is center of screen
    args = request.args
    real_args = ['polyline', 'reputation', 'title', 'description']
    if set(args) != set(real_args):
        return json.dumps({'status': 'error', 'status_extended': f'This function takes {len(real_args)} arguments: {real_args}'})
    polyline = args['polyline']
    reputation = args['reputation']
    title = args['title']
    description = args['description']
    # Connect to SQL Server
    cnx = None
    try:
        cnx = connect()
    except sql.Error as e:
        return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

    cursor = cnx.cursor(dictionary=True)
    query = ("INSERT INTO routes (ST_LineFromEncodedPolyline(polyline),reputation,title,description)"
                "VALUES (%s, %s,%s,%s)")
    # Do the query
    cursor.execute(query, [polyline, reputation,title,description])
    ret_val = cursor.fetchall()
    # Add distance from query point to return
    cursor.close()
    cnx.close()
    return json.dumps({"status": 'success', 'status_extended': '', 'return': ret_val})



@api.route('/api/reports')
def get_reports():
    # x,y is center of screen
    args = request.args
    if len(args) != 3:
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
    else:
        if 'lat' not in args.keys() or ('lng' not in args.keys()) or ('r' not in args.keys()):
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
        else:
            lat = float(args['lat'])
            lng = float(args['lng'])
            r = float(args['r'])
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor(dictionary=True)
            query = ("SELECT reports.id as rid, lat, lng, text, imgpath, score, userid, reporttype, timestamp, title, users.firstname as firstname,users.lastname as lastname "
                     "FROM reports "
                     "JOIN users on reports.userid=users.id "
                     "WHERE (ABS(lat-%s) <= %s) AND (ABS(lng-%s) <= %s) "
                     "ORDER BY POWER(lat-%s, 2) + POWER(lng-%s, 2) ASC")
            # Do the query
            cursor.execute(query, [float(lat), float(r), float(lng), float(r), float(lat), float(lng)])
            ret_val = cursor.fetchall()
            # Add distance from query point to return
            for row in ret_val:
                row["lat"] = float(row['lat'])
                row['lng'] = float(row['lng'])
                row["timestamp"] = datetime.datetime.strftime(row["timestamp"], '%Y-%m-%d %H:%M:%S')
                row['dst'] = geopy.distance.distance((row['lat'],row['lng'] ), (float(lat), float(lng))).km
            cursor.close()
            cnx.close()
            return json.dumps({"status": 'success', 'status_extended': '', 'return': ret_val})

@api.route('/api/messages')
def get_messages():
    args = request.args
    if len(args) != 2:
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 2 arguments: userid and userid2'})
    else:
        if 'userid' not in args.keys() or 'userid2' not in args.keys():
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 2 arguments: userid and userid2'})
        else:
            userid = int(args['userid'])
            userid2 = int(args['userid2'])
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                print(e)
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor(dictionary=True)
            query = ("SELECT messages.id as mid,userfromid,u1.firstname as userfromfirst, u1.lastname as userfromlast,usertoid, u2.firstname as usertofirst, "
                     "u2.lastname as usertolast, u1.profilepicturepath as userfrompic, u2.profilepicturepath as usertopic, message, timestamp "
                     "FROM messages "
                     "JOIN users as u1 ON userfromid=u1.id "
                     "JOIN users as u2 ON usertoid=u2.id "
                     "WHERE (userfromid = %s AND usertoid = %s) OR (userfromid = %s AND usertoid = %s) ")

            # Do the query
            cursor.execute(query, (int(userid), int(userid2), int(userid2), int(userid)))
            ret_val = cursor.fetchall()
            # Add distance from query point to return

            cursor.close()
            cnx.close()
            for val in ret_val:
                if(val["userfromid"] == userid):
                    val["otheruserpic"] = val["usertopic"]
                elif(val["usertoid"] == userid):
                    val["otheruserpic"] = val["userfrompic"]
                else:
                    print("What? Fail in messages call")
                del(val["usertopic"])
                del(val["userfrompic"])
                val["timestamp"] = datetime.datetime.strftime(val["timestamp"], '%Y-%m-%d %H:%M:%S')
            # del(latest[int(userid)])
            return json.dumps({"status": 'success', 'status_extended': '', 'return': ret_val})


@api.route('/api/preview')
def get_preview():
    args = request.args
    if len(args) != 1:
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 1 arguments: userid'})
    else:
        if 'userid' not in args.keys():
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 1 arguments: userid'})
        else:
            userid = int(args['userid'])
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                print(e)
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor(dictionary=True)

            query = ("SELECT messages.id as mid,userfromid,u1.firstname as userfromfirst, u1.lastname as userfromlast,usertoid, u2.firstname as usertofirst, "
                     "u2.lastname as usertolast, u1.profilepicturepath as userfrompic, u2.profilepicturepath as usertopic,message, timestamp "
                     "FROM messages "
                     "JOIN users as u1 ON userfromid=u1.id "
                     "JOIN users as u2 ON usertoid=u2.id "
                     "WHERE userfromid = %s OR usertoid = %s")
            # Do the query
            cursor.execute(query, (int(userid), int(userid)))
            ret_val = cursor.fetchall()
            # Add distance from query point to return
            latest = {}
            print(repr(ret_val))
            for row in ret_val:
                dict_insert = {'id': row["mid"], 'message': row["message"], 'timestamp': row["timestamp"]}
                otheruser = None
                if row["userfromid"] == int(userid):
                    otheruser = row["usertoid"]
                    dict_insert['name'] = row["usertofirst"] + " " + row["usertolast"]
                    dict_insert["otheruserpic"] = row["usertopic"]
                elif row["usertoid"] == int(userid):
                    print("SECOND IF")
                    otheruser = row["userfromid"]
                    dict_insert['name'] = row['userfromfirst'] + " " + row['userfromlast']
                    dict_insert["otheruserpic"] = row["userfrompic"]
                else:
                    print("Not by user")
                if otheruser in latest.keys():
                    if row["timestamp"] >= latest[otheruser]["timestamp"]:
                        latest[otheruser] = dict_insert
                        print("1")
                else:
                    latest[otheruser] = dict_insert
                    print("2")
            cursor.close()
            cnx.close()
            for otherid in latest.keys():
                latest[otherid]["timestamp"] = datetime.datetime.strftime(latest[otherid]["timestamp"], '%Y-%m-%d %H:%M:%S')
            # del(latest[int(userid)])
            return json.dumps({"status": 'success', 'status_extended': '', 'return': latest})


@api.route('/api/news')
def get_news():
    # x,y is center of screen
    args = request.args

    if (len(args) != 3):
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
    else:
        if ('lat' not in args.keys() or ('lng' not in args.keys()) or ('r' not in args.keys())):
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: lat and lng and r'})
        else:
            lat = float(args['lat'])
            lng = float(args['lng'])
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                print(e)
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor(dictionary=True)
            query = ("SELECT id, title, contents, severity, timestamp, lat, lng, radius "
                     "FROM news "
                     "WHERE (ABS(lat - %s) <= radius) AND (ABS(lng - %s) <= radius) "
                     "ORDER BY timestamp DESC")

            # Do the query
            cursor.execute(query, [lat, lng])
            ret_val = cursor.fetchall()
            for val in ret_val:
                val['lat'] = float(val['lat'])
                val['lng'] = float(val['lng'])
                val["timestamp"] = datetime.datetime.strftime(val["timestamp"], '%Y-%m-%d %H:%M:%S')
            # Close connection
            cursor.close()
            cnx.close()

            return json.dumps({"status": 'success', 'status_extended': '', 'return': ret_val})


@api.route('/api/send_message')
def send_message():
    args = request.args

    if (len(args) != 3):
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: userfromid, usertoid, message'})
    else:
        if ('userfromid' not in args.keys() or ('usertoid' not in args.keys()) or ('message' not in args.keys())):
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 3 arguments: userfromid, usertoid, message'})
        else:
            userfromid = int(args['userfromid'])
            usertoid = int(args['usertoid'])
            message = str(args['message'])
            # Connect to SQL Server
            cnx = None
            try:
                cnx = connect()
            except sql.Error as e:
                print(e)
                return json.dumps({'status': 'error', 'status_extended': 'Couldnt connect to sql database'})

            cursor = cnx.cursor()
            query = ("INSERT INTO messages (userfromid, usertoid, message) "
                     "VALUES (%s , %s , %s)")

            # Do the query
            try:
                cursor.execute(query, [userfromid, usertoid, message])
                cnx.commit()
            except:
                return json.dumps({"status": 'error', 'status_extended': 'Failed to submit the insert query'})
            # Close connection
            cursor.close()
            cnx.close()
            return json.dumps({"status": 'success', 'status_extended': ''})


@api.route('/api/send_poi')
def send_poi():
    args = request.args
    real_args = ["lat", "lng", "title", "description", "userid"]
    if (len(args) != 5):
        return json.dumps({'status': 'error', 'status_extended': 'This function takes 5 arguments: lat, lng, title, description, userid'})
    else:
        if (set(real_args) != set(args)):
            return json.dumps({'status': 'error', 'status_extended': 'This function takes 5 arguments: lat, lng, title, description, userid'})
        else:
            lat = float(args['lat'])
            lng = float(args['lng'])
            title = args['title']
            description = args['description']
            userid = int(args['userid'])
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
            try:
                cursor.execute(query, [lat, lng, title, description, userid])
                cnx.commit()
            except:
                return json.dumps({"status": 'error', 'status_extended': 'Failed to submit the insert query'})

            # Close connection
            cursor.close()
            cnx.close()
            return json.dumps({"status": 'success', 'status_extended': ''})


@api.route('/html/<path:path>')
def send_js(path):
    return send_from_directory('html', path)


@api.route("/api/fire_data")
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
