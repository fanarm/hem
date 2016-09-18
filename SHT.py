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

import smbus
import time

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

