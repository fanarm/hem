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
import smbus
import time
import datetime
import RPi.GPIO as GPIO
import os
import posix_ipc as ipc

REGULAR_DATA_FILE = "/home/pi/hem/log/pmth.log"
SHM_NAME_HEM_PRESENT_DATA = "/hem_data"
SHM_SIZE_HEM_PRESENT_DATA = 64
SHM_NAME_HEM_APMI_DATA = "/hem_apmi"
SHM_SIZE_HEM_APMI_DATA = 16
LOG_FILE = "/home/pi/hem/log/hem.log"
PLOT_LOG_FILE_NAME_BASE = "/home/pi/hem/log/pmth_plot_"
RUNNING_TIME_OFFSET_SEC = 6.4

## Hourly array to set polling interval
TARGET_SAMPLES_OVER_HOURS = [  12,  12,  2,  2,  2,  2,  3, 12, 12, 12,  6,  6, 
                               6,  6,  6,  6, 12, 12, 12, 12, 12, 12,  6,  3]
PM25_SMOOTHING_SAMPLES = 5
PM25_MAX_RETRIES = 5
AP_MI_SENSOR_CONSTANT = 2.428

class PMSensor :
    """ Class for PM2.5 sensor """
    def __init__(self, portNameStr, sleepGPIO) :
        self.port = serial.Serial(portNameStr, baudrate=9600,timeout=3.0)
        self.sleepgpio = sleepGPIO
    def initialize(self) :
        GPIO.setup(self.sleepgpio,GPIO.OUT)
        GPIO.output(self.sleepgpio,1)
        time.sleep(10)
        GPIO.output(self.sleepgpio,0)
        time.sleep(5)
        self.port.readall()
    def wake(self) :
        GPIO.output(self.sleepgpio,1)
    def sleep(self) :
        GPIO.output(self.sleepgpio,0)
    def flush(self) :
        self.port.readall()
    def readPM25(self) :
        pm25_data = []
        self.wake()
        pm25_retry_count = 0
        while len(pm25_data)<PM25_SMOOTHING_SAMPLES and pm25_retry_count<PM25_MAX_RETRIES :
            need_recover = False
            rcv = self.port.read(32)
            if len(rcv) < 32 :
                print_log_with_time(LOG_FILE,'a',"[Error] G5 PM2.5 sensor receiving error. Less than 32 bytes.\n")
                need_recover = True
            elif rcv[0] != '\x42' or rcv[1] != '\x4d' or rcv[2] != '\x00' or rcv[3] != '\x1c' :
                print_log_with_time(LOG_FILE,'a',"[Error] G5 PM2.5 sensor receiving error. Data truncated.\n")
                need_recover = True
            else :
                ## pm1=ord(rcv[10])*256+ord(rcv[11])
                pm25=ord(rcv[12])*256+ord(rcv[13])
                pm25_data.append(pm25)
            if need_recover :
                self.sleep()
                self.port.readall()
                ## pm1 = "n/a"
                pm25 = "n/a"
                sleep(2)
                self.port.readall()
                pm25_retry_count += 1
                self.wake()
        self.sleep()
        if len(pm25_data)>0 :
            return sum(pm25_data)/PM25_SMOOTHING_SAMPLES
        else :
            return 0

class SHT :
    """ Class for temperature and humidity sensor """
    def __init__(self,i2c_num) :
        self.bus = smbus.SMBus(i2c_num)
    def readTemp(self) :
        self.bus.write_byte(0x40,0xf3)
        time.sleep(0.2)
        vt = self.bus.read_byte(0x40)
        ## print "T raw readig: "+repr(vt)
        return int(-46.85 + 175.72*vt/256)
    def readHumid(self) :
        self.bus.write_byte(0x40,0xf5)
        time.sleep(0.2)
        vh = self.bus.read_byte(0x40)
        ## print "RH raw readig: "+repr(vh)
        return int(-6 + 125*vh/256)

class ap_mi :
    """ Class for temperature and humidity sensor /dev/rfcomm0 """
    def __init__(self,devname) :
        self.port = serial.Serial(devname, baudrate=9600,timeout=1.5)
    def bytesToStr(self,bytelist) :
        return ''.join(chr(c) for c in bytelist)
    def strToBytes(self,rcvstr) :
        return list(ord(c) for c in rcvstr)
    def sendFixedOutput(self, value) :
        txstr = self.bytesToStr([0x65,0x90,value,0,(0x90+value)%256])
        self.port.write(txstr)
        rxstr = self.port.read(5)
        return (ord(rxstr[2])==value)

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

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
pms = PMSensor("/dev/ttyAMA0",18)
pms.initialize()
ths = SHT(1)
apmi = ap_mi("/dev/rfcomm0")
print_log_with_time(LOG_FILE,'a',"[Info] hem.py starts polling loop.\n")
while True:
    pm25s = pms.readPM25()
    t = ths.readTemp()
    h = ths.readHumid()
    curtime = datetime.datetime.now()
    timestr = curtime.strftime("%Y/%m/%d %H:%M:%S")
    rec = timestr + " PM2.5:"+repr(pm25s)+ " Temp:"+repr(t)+ " RH:"+repr(h)+"%\n"
    print rec
    print_log(REGULAR_DATA_FILE,'w',rec)
    if apmi.sendFixedOutput(int(pm25s/AP_MI_SENSOR_CONSTANT))!=True :
        print_log_with_time(LOG_FILE,'a',"[Error] hem.py fails to update PM2.5 sensor on AP_mi.\n")
    shared_memory_write(SHM_NAME_HEM_PRESENT_DATA, SHM_SIZE_HEM_PRESENT_DATA,
                        rec)
    plotfile = PLOT_LOG_FILE_NAME_BASE+curtime.strftime("%Y_%m_%d")+".log"
    if not os.path.exists(plotfile) :
        print_log(plotfile,'w',"Date Time PM2.5 Temp Humidity\n")
    print_log(plotfile,'a',timestr+" "+repr(pm25s)+" "+repr(t)+" "+repr(h)+"\n")
    time.sleep(calculate_sleep_target(curtime))
    pms.flush()
    
    
