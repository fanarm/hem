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

import serial
import time
import datetime
import RPi.GPIO as GPIO
import os
import posix_ipc as ipc
import logging
import subprocess
import PMSensor
import SHT
import ap_mi

REGULAR_DATA_FILE = "/home/pi/hem/log/pmth.log"
SHM_NAME_HEM_PRESENT_DATA = "/hem_data"
SHM_SIZE_HEM_PRESENT_DATA = 64
#SHM_NAME_HEM_APMI_STATUS = "/hem_apmi"
#SHM_SIZE_HEM_APMI_STATUS = 64
PID_FILE_BT_RFCOMM = "/var/run/hemapmi.pid"
LOG_FILE = "/home/pi/hem/log/hem.log"
PLOT_LOG_FILE_NAME_BASE = "/home/pi/hem/log/pmth_plot_"
RUNNING_TIME_OFFSET_SEC = 6.4
BTH_NAME = 'hci0'
BTS_ADDR = '98:D3:32:30:39:59'
BT_UART_DEV_NAME = '/dev/rfcomm0'

## Hourly array to set polling interval
TARGET_SAMPLES_OVER_HOURS = [  6,  6,  6,  6,  6,  6,  12, 30, 30, 12,  12,  12, 
                               30,  12,  12,  12, 30, 30, 60, 60, 60, 60,  30,  6]

AP_MI_SENSOR_CONSTANT = 2.428


def bluetoothRecovery() :
    logging.getLogger().info("hem.py tries to reconnect to AP_mi via rfcomm.") 
    subprocess.call(['hciconfig',BTH_NAME,'reset'])
    time.sleep(10)
    proc = subprocess.Popen(['rfcomm','connect',BTH_NAME,BTS_ADDR])
    logging.getLogger().info("Rfcomm process %d started",proc.pid) 
    print_log(PID_FILE_BT_RFCOMM,'w',repr(proc.pid))
    #TODO: if succeeds, need update pid file for rfcomm so that the process could be killed when stopping hem.


def print_log(log_file_name, openmode, log_string) :
    logfile = open(log_file_name, openmode)
    logfile.write(log_string)
    logfile.close()

def print_log_with_time(log_file_name, openmode, log_string) :
    curtime = datetime.datetime.now()
    timestr = curtime.strftime("%Y/%m/%d %H:%M:%S ")
    print_log(log_file_name, openmode, timestr+log_string)

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

def startMonitoring() :
    logging.basicConfig(filename=LOG_FILE,level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s')
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        pms = PMSensor.PMSensor("/dev/ttyAMA0",18)
        pms.initialize()
        ths = SHT.SHT(1)
        apmi = ap_mi.ap_mi(BT_UART_DEV_NAME,AP_MI_SENSOR_CONSTANT)
        if os.path.exists(BT_UART_DEV_NAME) :
            apmi.open()
        logging.getLogger().info("hem.py starts polling loop") 
        while True:
            pm25s = pms.readPM25()
            t = ths.readTemp()
            h = ths.readHumid()
            curtime = datetime.datetime.now()
            timestr = curtime.strftime("%Y/%m/%d %H:%M:%S")
            rec = timestr + " PM2.5:"+repr(pm25s)+ " Temp:"+repr(t)+ " RH:"+repr(h)+ "% "
            if os.path.exists(BT_UART_DEV_NAME) :
                if not apmi.opened :
                    apmi.open()
                if apmi.sendFixedOutput(pm25s)==False :
                    logging.getLogger().error("hem.py fails to update PM2.5 sensor on AP_mi.") 
                    apmi.close()
                    bluetoothRecovery()
                    rec = rec + "APMI:Fail\n"
                else :
                    rec = rec + "APMI:OK\n"
            else :
                bluetoothRecovery()
                rec = rec + "APMI:Fail\n"
            shared_memory_write(SHM_NAME_HEM_PRESENT_DATA, SHM_SIZE_HEM_PRESENT_DATA, rec)
            plotfile = PLOT_LOG_FILE_NAME_BASE+curtime.strftime("%Y_%m_%d")+".log"
            if not os.path.exists(plotfile) :
                print_log(plotfile,'w',"Date Time PM2.5 Temp Humidity\n")
            print_log(plotfile,'a',timestr+" "+repr(pm25s)+" "+repr(t)+" "+repr(h)+"\n")
            time.sleep(calculate_sleep_target(curtime))
            pms.flush()
    except (Exception,KeyboardInterrupt):
        logger = logging.getLogger()
        logger.exception("Fatal exception in hem.py execution") 

if __name__ == "__main__" :
   startMonitoring()
    
