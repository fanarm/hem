import serial
import time

AVAIL_SOURCES = ["SAT","HDP","DVR","DVD","TV/CBL"]

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
        self.sendCommand("PW?,SI?,MU?")
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
        if volUp :
           self.sendCommand("MVUP")
        else :
           self.sendCommand("MVDOWN")
    def setMute(self, muteOn) :
        if muteOn :
           self.sendCommand("MUON")
        else :
           self.sendCommand("MUOFF")
