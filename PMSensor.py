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
import RPi.GPIO as GPIO
import logging

PM25_SMOOTHING_SAMPLES = 5
PM25_MAX_RETRIES = 5

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
                #print_log_with_time(LOG_FILE,'a',"[Error] G5 PM2.5 sensor receiving error. Less than 32 bytes.\n")
                logging.getLogger().error("G5 PM2.5 sensor receiving error. Less than 32 bytes.") 
                need_recover = True
            elif rcv[0] != '\x42' or rcv[1] != '\x4d' or rcv[2] != '\x00' or rcv[3] != '\x1c' :
                #print_log_with_time(LOG_FILE,'a',"[Error] G5 PM2.5 sensor receiving error. Data truncated.\n")
                logging.getLogger().error("G5 PM2.5 sensor receiving error. Data truncated.")
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
        numSample = len(pm25_data)
        if numSample >0 :
            return sum(pm25_data)/numSample
        else :
            return 0

