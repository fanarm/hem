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
import os

def modVout(orig) :
    if orig<10 :
        return orig*5
    if orig<20 :
        return orig*3
    if orig<40 :
        return orig*1.5
    return orig

def headerFinder(ttyPort) :
    while True :
        read = port.read(1)
        if read[0] == '\xaa' :
            read = port.read(6)
            if read[5] == '\xff' :
                return
    

port = serial.Serial("/dev/rfcomm0", baudrate=2400,timeout=3)
print "Port opened."
headerFinder(port)
while True :
    rcv = port.read(7)
    if rcv[0] != '\xaa' or rcv[6] != '\xff':
        headerFinder(port)
        continue
    origV = ord(rcv[1])*256+ord(rcv[2])
    modV = modVout(origV)
    modVH = modV>>8
    modVL = modV & 255
    refVH = ord(rcv[3])
    refVL = ord(rcv[4])
    veri = (modVH+modVL+refVH+refVL)&255
    wrt = rcv[0]+''.join(map(lambda b: chr(b), [modVH, modVL, refVH, refVL,veri]))+rcv[6]
    port.write(wrt)
    origstr = ':'.join(map(lambda c: format(ord(c), "02x"), rcv))
    modstr = ':'.join(map(lambda c: format(ord(c), "02x"), wrt))
    print origstr+" --> "+modstr

    
