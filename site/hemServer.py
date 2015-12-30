#!/usr/bin/python

from flask import Flask
from flask import render_template, send_from_directory
import re
import datetime
import posix_ipc as ipc
import os

LOG_FILE_PATH = "/home/pi/hem/log/"
REGULAR_LOG_REGEX = "(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) PM2\.5:(\d+) Temp:(\d+) RH:(\d+)%"
SHM_NAME_HEM_PRESENT_DATA = "/hem_data"
SHM_SIZE_HEM_PRESENT_DATA = 256
CHART_LOCAL_PATH = "/home/pi/hem/pic/"
CHART_URL_PREFIX = "/chart/"

def shared_memory_write(shm_name, shm_size, data) :
    shm = ipc.SharedMemory(shm_name, ipc.O_CREAT,
                           0600, shm_size, False)
    os.write(shm.fd, data)
    shm.close_fd()

def shared_memory_readline(shm_name, shm_size) :
    shm = ipc.SharedMemory(shm_name, ipc.O_CREAT,
                           0600, shm_size, False)
    shmfile = os.fdopen(shm.fd)
    res = shmfile.readline()
    ## print "shm read length: "+str(len(res))
    shmfile.close()
    return res

app = Flask(__name__)

@app.route("/") 
def showStatus():
   recline = shared_memory_readline(SHM_NAME_HEM_PRESENT_DATA, SHM_SIZE_HEM_PRESENT_DATA)
   rec_mo = re.search(REGULAR_LOG_REGEX, recline)
   timestamp = rec_mo.group(1)
   pmvalue = rec_mo.group(2)
   tvalue = rec_mo.group(3)
   rhvalue = rec_mo.group(4)
   return render_template('hem_template.html', ts=timestamp, pm=pmvalue, t=tvalue, rh=rhvalue)

@app.route("/history.html")
def serveHistory():
   curtime = datetime.datetime.now()
   filename = curtime.strftime("pmth_plot_%Y_%m_%d.log")
   logfile = open(LOG_FILE_PATH+filename,'r')
   lines = logfile.readlines()
   return render_template('history_template.html', header=lines[0], entries=lines[1:])

@app.route("/chart/<path:filename>")
def serveChart(filename):
   return send_from_directory("/home/pi/hem/pic", filename)

@app.route("/chartnow/<path:filename>")
def serveNowChart(filename):
   curtime = datetime.datetime.now()
   timestr = curtime.strftime("_%Y_%m_%d.png")
   return send_from_directory("/home/pi/hem/pic", filename+timestr)

@app.after_request
def add_header(response):
   response.headers['Cache-Control']='no-cache,no-store,must-revalidate'
   response.headers['Pragma']='no-cache'
   return response

if __name__ == "__main__" :
   app.run('0.0.0.0')

