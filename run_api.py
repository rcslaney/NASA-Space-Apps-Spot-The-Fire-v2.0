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


app = Flask(__name__, static_url_path='')

app.register_blueprint(api)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
