#!/usr/bin/python

'''
  Copyright 2016, Xun Jiang

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

from flask import Flask, request
from flask import render_template, send_from_directory
import re
import datetime
import posix_ipc as ipc
import os
import sched
import time
import subprocess
import threading
import avr
import logging
from logging import Formatter

SERVER_PORT = 30933

LOG_FILE_PATH = "/home/pi/hem/log/"
REGULAR_LOG_REGEX = "(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) PM2\.5:(\d+) Temp:(\d+) RH:(\d+)% APMI:(\w+)"
SHM_NAME_HEM_PRESENT_DATA = "/hem_data"
SHM_SIZE_HEM_PRESENT_DATA = 256
CHART_LOCAL_PATH = "/home/pi/hem/pic/"
CHART_URL_PREFIX = "/chart/"
WOL_LOCK_FILE_NAME = "/run/lock/nas.wol.lock"
WOL_SCRIPT_FILE_NAME = "/home/pi/hem/wol.sh"
SERVER_LOG_FILE_NAME = LOG_FILE_PATH + "server.log"
AVR_USB_PORT_NAME = "/dev/ttyUSB0"
KODI_EXE_PATH = "/usr/bin/kodi"

wol_timer = None
wol_on = False
wol_planned_off = None
wol_pid = None
kodi_shell_pid = None
avr2809 = avr.avr(AVR_USB_PORT_NAME)

def stop_wol():
    global wol_pid
    global wol_on
    global wol_timer
    subprocess.call(['rm',WOL_LOCK_FILE_NAME])
    wol_pid = None
    wol_on = False
    wol_timer = None
    app.logger.debug("WOL lock file removed.")

def start_wol():
    global wol_pid
    global wol_on
    subprocess.call(['touch',WOL_LOCK_FILE_NAME])
    wol_pid = subprocess.Popen([WOL_SCRIPT_FILE_NAME]).pid
    wol_on = True
    app.logger.debug("WOL lock file created.")

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
   if rec_mo == None :
      timestamp = pmvalue = tvalue = rhvalue = apmiRes = "n.a."
   else :
      timestamp = rec_mo.group(1)
      pmvalue = rec_mo.group(2)
      tvalue = rec_mo.group(3)
      rhvalue = rec_mo.group(4)
      apmiRes = rec_mo.group(5)
   return render_template('hem_template.html', ts=timestamp, pm=pmvalue, t=tvalue, rh=rhvalue, ar=apmiRes)

@app.route("/history.html")
def serveHistory():
   curtime = datetime.datetime.now()
   filename = curtime.strftime("pmth_plot_%Y_%m_%d.log")
   logfile = open(LOG_FILE_PATH+filename,'r')
   lines = logfile.readlines()
   return render_template('history_template.html', header=lines[0], entries=lines[1:])

@app.route("/log.html")
def serveLog():
   logfile = open(LOG_FILE_PATH+"hem.log",'r')
   lines = logfile.readlines()
   return render_template('log_template.html', entries=lines)

@app.route("/config.html")
@app.route("/nasconf.html", methods=['GET','POST'])
def serveNasConfig():
   global wol_on
   global wol_planned_off
   global wol_timer
   global kodi_shell_pid
   if request.method == 'POST' :
      if 'NAS_act_sel' in request.form : 
         extend_time = request.form['NAS_act_sel']
         if wol_timer != None :
            wol_timer.cancel()
         if extend_time == '0' :
            stop_wol()
         else :
            start_wol()
            wol_planned_off = time.localtime(time.time()+int(extend_time)*60)
            wol_timer = threading.Timer(int(extend_time)*60,stop_wol)
            wol_timer.start()
#           if extend_time != 'forever' :
#              Timer(int(extend_time)*60,stop_wol,()).start()
      elif 'AVR_act_vol' in request.form :
         avr_cmd = request.form['AVR_act_vol']
         print "avr_cmd:"+avr_cmd
         if avr_cmd == "volup" :
            avr2809.setVolume(True)
         elif avr_cmd == "voldown" :
            avr2809.setVolume(False)
         elif avr_cmd == "mute" :
            avr2809.setMute(avr2809.status["Mute"] == "OFF")
      elif 'AVR_act_ctn' in request.form :
         avr_cmd = request.form['AVR_act_ctn']
         print "avr_cmd:"+avr_cmd
         if avr_cmd == "kodi" :
            kodi_shell_pid = subprocess.Popen(["sudo", "su", "-c "+KODI_EXE_PATH, "pi"])
      elif 'AVR_act_sel' in request.form :
         avr_cmd = request.form['AVR_act_sel']
         print "avr_cmd:"+avr_cmd
         if avr_cmd in avr.AVAIL_SOURCES :
            if avr2809.status["Power"] != "on" :
               avr2809.setPower(True)
            avr2809.setSource(avr_cmd)
         elif avr_cmd == "off" :
            avr2809.setPower(False)
   else :
      avr2809.updateStatus()
   if wol_on :
      if wol_planned_off == None :
         wolstatus = "On"
      else :
         wolstatus = time.strftime('On till %X %x %Z', wol_planned_off)
   else :
      wolstatus = "Off"
   if avr2809.status["Power"] == 'on' :
      avrstatus = "Power: On, Source: %s, Mute: %s, Volume: %d" % (avr2809.status["Source"],avr2809.status["Mute"],avr2809.status["Volume"])
   else :
      avrstatus = "Power: Off"
   return render_template('nasconf_template.html', wol_status=wolstatus, avr_status=avrstatus)

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
   file_handler = logging.FileHandler(SERVER_LOG_FILE_NAME)
   file_handler.setLevel(logging.DEBUG)
   file_handler.setFormatter(Formatter('%(asctime)s %(levelname)s: %(message)s'))
   app.logger.addHandler(file_handler)
   app.logger.setLevel(logging.DEBUG)
   app.logger.debug("HEM server started.")
   app.run(debug=True, use_debugger=True, host='0.0.0.0',port=SERVER_PORT)




