from flask import Flask
from flask import render_template
import re

REGULAR_LOG_FILE = "/home/pi/hem/log/pmth.log"
REGULAR_LOG_REGEX = "(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) PM2\.5:(\d+) Temp:(\d+) RH:(\d+)%"

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
   return render_template('hem_template.html', ts=timestamp, pm=pmvalue, t=tvalue, rh=rhvalue)

@app.route("/chart/<path:filename>")
def servePics(filename):
   return send_from_directory()

if __name__ == "__main__" :
   app.run('0.0.0.0')

