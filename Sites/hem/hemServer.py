#!/usr/bin/python

from flask import Flask
from flask import render_template, send_from_directory
import re
import datetime

REGULAR_LOG_FILE = "/home/pi/hem/log/pmth.log"
REGULAR_LOG_REGEX = "(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) PM2\.5:(\d+) Temp:(\d+) RH:(\d+)%"
CHART_LOCAL_PATH = "/home/pi/hem/pic/"
CHART_URL_PREFIX = "/chart/"

app = Flask(__name__)

@app.route("/") 
def showStatus():
   reglogfile = open(REGULAR_LOG_FILE,'r')
   recline = reglogfile.readline()
   reglogfile.close()
   rec_mo = re.search(REGULAR_LOG_REGEX, recline)
   timestamp = rec_mo.group(1)
   pmvalue = rec_mo.group(2)
   tvalue = rec_mo.group(3)
   rhvalue = rec_mo.group(4)
   curtime = datetime.datetime.now()
   timestr = curtime.strftime("%Y_%m_%d")
   return render_template('hem_template.html', ts=timestamp, pm=pmvalue, 
                           pm25_chart_path=CHART_URL_PREFIX+"hem_pm25_"+timestr+".png",
                           t=tvalue, rh=rhvalue,
                           t_chart_path=CHART_URL_PREFIX+"hem_temp_"+timestr+".png",
                           rh_chart_path=CHART_URL_PREFIX+"hem_humid_"+timestr+".png" )

@app.route("/chart/<path:filename>")
def servePics(filename):
   return send_from_directory("/home/pi/hem/pic", filename)

if __name__ == "__main__" :
   app.run('0.0.0.0')

