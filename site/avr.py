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

AVAIL_SOURCES = ["SAT","HDP","DVR","DVD","TV/CBL"]

MVMIN = 0
MVMAX = 90

class avr:
    def __init__(self, portname) :
        self.port = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=0.5)
        self.port.readall()
        self.powerOn = False
        self.status = dict([])
    def parseStatus(self, respStr) :
        lines = respStr.split('\r')
        for line in lines :
          if len(line) > 2:
            if line[0:2] == "PW" :
              if line[2:4] == "ON" :
                self.status.update({"Power":"on"})
                self.powerOn = True
              else :
                self.status.update({"Power":"standby"})
                self.powerOn = False
            elif line[0:2] == "SI" :
                self.status.update({"Source":line[2:]})
            elif line[0:2] == "MU" :
                self.status.update({"Mute":line[2:]})
            elif line[0:2] == "MV" and line[2] != 'M' :
                self.status.update({"Volume":int(line[2:4])})
        return  
    def readResp(self) :
        rcv = ''
        while True :
           rcvnew = self.port.read(64)
           if rcvnew == '' :
              break
           rcv += rcvnew
        self.parseStatus(rcv)
        return rcv
    def sendCommand(self, cmdStr, extraWait=0) :
        list = cmdStr.split(',')
        for cmd in list :
           self.port.write(cmd+'\r')
        if extraWait != 0 :
           time.sleep(extraWait)
        return self.readResp()
    def updateStatus(self) :
        if not "Power" in self.status :
           self.status.update({"Power":"n.a."})
        if not "Source" in self.status :
           self.status.update({"Source":"n.a."})
        if not "Mute" in self.status :
           self.status.update({"Mute":"n.a."})
        if not "Volume" in self.status :
           self.status.update({"Volume":MVMIN})
        self.sendCommand("PW?,SI?,MU?,MV?")
        return 
    def setPower(self, powerOn) :
        if powerOn :
           self.sendCommand("PWON")
        else :
           self.sendCommand("PWSTANDBY")
    def setSource(self, source) :
        if source in AVAIL_SOURCES :
           self.sendCommand("SI"+source,1.5)
    def setVolume(self, volUp) :
        vol = self.status["Volumn"]
        if volUp :
           vol += 5
           if vol > MVMAX :
              vol = MVMAX
        else :
           vol -= 5
           if vol < MVMIN :
              vol = MVMIN
        self.sendCommand("MV"+str(vol))
    def setMute(self, muteOn) :
        if muteOn :
           self.sendCommand("MUON")
        else :
           self.sendCommand("MUOFF")
