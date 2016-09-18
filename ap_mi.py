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
import logging

class ap_mi :
    """ Class for AirPurifier dust sensor connected via Bluetooth /dev/rfcomm0 """
    def __init__(self,devname,sensor_const) :
        self.devname = devname
        self.opened = False
        self.port = None
        self.sensor_const = sensor_const
    def open(self) :
        try:
            self.port = serial.Serial(self.devname, baudrate=9600,timeout=1.5)
            self.opened = True
        except serial.SerialException :
            logging.getLogger().exception("Bluetooth serial exception when opening the port.") 
            self.opened = False
    def close(self) :
        if self.port != None :
            self.port.close()
        self.port = None
        self.opened = False
    def bytesToStr(self,bytelist) :
        return ''.join(chr(c) for c in bytelist)
    def strToBytes(self,rcvstr) :
        return list(ord(c) for c in rcvstr)
    def sendFixedOutput(self, value) :
        raw = int(value/self.sensor_const)
        if raw>255 :
            raw = 255
        txstr = self.bytesToStr([0x65,0x90,raw,0,(0x90+raw)%256])
        try:
            self.port.write(txstr)
            rxstr = self.port.read(5)
            if len(rxstr)>2 :
                return (ord(rxstr[2])==raw)
            else :
                logging.getLogger().warning("Bluetooth serial read error after writing. Less data than expected.")
                return False
        except serial.SerialException :
            logging.getLogger().exception("Bluetooth serial exception when accessing the port.") 
            return False
    def updateSensorConst(self, value) :
        self.sensor_const = value
