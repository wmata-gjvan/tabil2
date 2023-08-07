import csv
import os
from colorama import Fore
import json
import copy
import requests

from flask import Flask, Response
from flask import request
import webbrowser
app = Flask(__name__, static_url_path='/static')

listOfOptions = [""]
i=0
for row in csv.reader(open("Track Circuits.csv")):
    if i==0: 
        listOfOptions.clear()
        i+=1 
        continue
    listOfOptions.append(row)
    i+=1
#Flask web application routes
@app.route("/")
def home():
    return open('ui.html').read()
@app.route("/getOptions")
def getOptions():
    return json.dumps([row[0] for row in listOfOptions])
@app.route("/createConfigFile")
def config():
    stats = dict(station = request.args.get('station'),
    bufferTime = request.args.get('buffertime'),
    arrivalCountdown = request.args.get('arrcount'),
    platformCountdown = request.args.get('pltcount'),
    weekdaystart1 = request.args.get('weekdaystart1'),
    weekdayend1 = request.args.get('weekdayend1'),
    weekdaystart2 = request.args.get('weekdaystart2'),
    weekdayend2 = request.args.get('weekdayend2'),
    weekendstart1 = request.args.get('weekendstart1'),
    weekendend1 = request.args.get('weekendend1'),
    weekendstart2 = request.args.get('weekendstart2'),
    weekendend2 = request.args.get('weekendend2'))
    cfgfile = open("config.json", 'w')
    cfgfile.write(json.dumps(stats))
    return "success"
    
@app.route("/begin")
def begin():
    os.system("python tabil2.py")
    return "hello" & exit()

webbrowser.open('http://0.0.0.0:4000')