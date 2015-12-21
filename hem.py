#!/usr/bin/python

import serial
import smbus
import time
import datetime
import RPi.GPIO as GPIO
import os

REGULAR_DATA_FILE = "/home/pi/hem/log/pmth.log"
LOG_FILE = "/home/pi/hem/log/hem.log"
PLOT_LOG_FILE_NAME_BASE = "/home/pi/hem/log/pmth_plot_"
RUNNING_TIME_OFFSET_SEC = 6.4

## Hourly array to set polling interval
TARGET_SAMPLES_OVER_HOURS = [  2,  2,  2,  2,  2,  2,  3, 12, 12, 12,  6,  6, 
                               6,  6,  6,  6, 12, 12, 12, 12, 12, 12,  6,  3]
PM25_SMOOTHING_SAMPLES = 5
PM25_MAX_RETRIES = 5

def print_log(log_file_name, openmode, log_string) :
    logfile = open(log_file_name, openmode)
    logfile.write(log_string)
    logfile.close()

def print_log_with_time(log_file_name, openmode, log_string) :
    curtime = datetime.datetime.now()
    timestr = curtime.strftime("%Y/%m/%d %H:%M:%S ")
    print_log(log_file_name, openmode, timestr+log_string)

def calculate_sleep_target(timenow) :
    samples=TARGET_SAMPLES_OVER_HOURS[timenow.hour]
    interval=3600/samples
    sec_in_curhour = timenow.minute*60+timenow.second
    times=round(sec_in_curhour/interval)
    target_sec = times*interval
    if target_sec>sec_in_curhour :
        return target_sec-sec_in_curhour
    else :
        return interval

bus = smbus.SMBus(1)
port = serial.Serial("/dev/ttyAMA0", baudrate=9600,timeout=3.0)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18,GPIO.OUT)
GPIO.output(18,1)
time.sleep(10)
GPIO.output(18,0)
time.sleep(5)
port.readall()
print_log_with_time(LOG_FILE,'a',"[Info] hem.py starts execution.\n")
while True:
    pm25_data = []
    GPIO.output(18,1)
    pm25_retry_count = 0
    while len(pm25_data)<PM25_SMOOTHING_SAMPLES and pm25_retry_count<PM25_MAX_RETRIES :
        need_recover = False
        rcv = port.read(32)
        if len(rcv) < 32 :
            print_log_with_time(LOG_FILE,'a',"[Error] G5 PM2.5 sensor receiving error. Less than 32 bytes.\n")
            need_recover = True
        elif rcv[0] != '\x42' or rcv[1] != '\x4d' or rcv[2] != '\x00' or rcv[3] != '\x1c' :
            print_log_with_time(LOG_FILE,'a',"[Error] G5 PM2.5 sensor receiving error. Data truncated.\n")
            need_recover = True
        else :
            pm1=ord(rcv[10])*256+ord(rcv[11])
            pm25=ord(rcv[12])*256+ord(rcv[13])
        if need_recover :
            GPIO.output(18,0)
            port.readall()
            pm1 = "n/a"
            pm25 = "n/a"
            sleep(5)
            port.readall()
            pm25_retry_count += 1
            GPIO.output(18,1)
        else :
            pm25_data.append(pm25)
    GPIO.output(18,0)
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
    rec = timestr + " PM2.5:"+repr(pm25s)+ " Temp:"+repr(t)+ " RH:"+repr(h)+"%\n"
    ## print rec
    print_log(REGULAR_DATA_FILE,'w',rec)
    plotfile = PLOT_LOG_FILE_NAME_BASE+curtime.strftime("%Y_%m_%d")+".log"
    if not os.path.exists(plotfile) :
        print_log(plotfile,'w',"Date Time PM2.5 Temp Humidity\n")
    print_log(plotfile,'a',timestr+" "+repr(pm25s)+" "+repr(t)+" "+repr(h)+"\n")
    time.sleep(calculate_sleep_target(curtime))
    port.readall()
    
    
