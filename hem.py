#!/usr/bin/python

import serial
import smbus
import time
import datetime
import RPi.GPIO as GPIO
import os

REGULAR_LOG_FILE = "/home/pi/hem/log/pmth.log"
PLOT_LOG_FILE_NAME_BASE = "/home/pi/hem/log/pmth_plot_"
RUNNING_TIME_OFFSET_SEC = 6.4
TARGET_INTERVAL = 60
PM25_SMOOTHING_SAMPLES = 5
PLOT_INTERVAL_RATIO = 5

POLLING_INTERVAL_SEC = TARGET_INTERVAL - RUNNING_TIME_OFFSET_SEC
plot_rec_count = 0
pm25_data = []
bus = smbus.SMBus(1)
port = serial.Serial("/dev/ttyAMA0", baudrate=9600,timeout=3.0)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18,GPIO.OUT)
GPIO.output(18,1)
time.sleep(1.5)
GPIO.output(18,0)
time.sleep(1.5)
port.readall()
while True:
    need_recover = False
    GPIO.output(18,1)
    rcv = port.read(32)
    if len(rcv) < 32 :
        print "G5 receiving error. Less than 32 bytes."
        need_recover = True
    elif rcv[0] != '\x42' or rcv[1] != '\x4d' or rcv[2] != '\x00' or rcv[3] != '\x1c' :
        print "G5 receiving error."
        need_recover = True
    else :
        pm1=ord(rcv[10])*256+ord(rcv[11])
        pm25=ord(rcv[12])*256+ord(rcv[13])
    GPIO.output(18,0)
    if need_recover :
        port.readall()
        pm1 = "n/a"
        pm25 = "n/a"
    else :
        pm25_data.append(pm25)
        while len(pm25_data) > PM25_SMOOTHING_SAMPLES :
            pm25_data.pop(0)
        pm25s = sum(pm25_data)/PM25_SMOOTHING_SAMPLES
    ##v = bus.read_byte_data(0x40,0xe3)
    bus.write_byte(0x40,0xf3)
    time.sleep(0.2)
    vt = bus.read_byte(0x40)
    ## print "T raw readig: "+repr(vt)
    t = int(-46.85 + 175.72*vt/256)
    bus.write_byte(0x40,0xf5)
    time.sleep(0.2)
    vh = bus.read_byte(0x40)
    ## print "RH raw readig: "+repr(vh)
    h = int(-6 + 125*vh/256)
    curtime = datetime.datetime.now()
    timestr = curtime.strftime("%Y/%m/%d %H:%M:%S")
    rec = timestr + " PM2.5:"+repr(pm25)+ " Temp:"+repr(t)+ " RH:"+repr(h)+"%"
    print rec
    recstr = str(rec+'\n')
    regfile = open(REGULAR_LOG_FILE,'w')
    regfile.write(recstr)
    regfile.close()
    if plot_rec_count == PLOT_INTERVAL_RATIO - 1 :
        if not need_recover :
            plotfile = PLOT_LOG_FILE_NAME_BASE+curtime.strftime("%Y_%m_%d")+".log"
            if not os.path.exists(plotfile) :
                recfile = open(plotfile,'a')
                recfile.write("Date Time PM2.5 Temp Humidity\n")
            else :
                recfile = open(plotfile,'a')    
            recfile.write(timestr+" "+repr(pm25s)+" "+repr(t)+" "+repr(h)+"\n")
            recfile.close()
        plot_rec_count = 0
    else :
        plot_rec_count += 1
    time.sleep(POLLING_INTERVAL_SEC)
    port.readall()
    
    
