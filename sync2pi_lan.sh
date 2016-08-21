#!/bin/bash
scp ~/Smarthome/hem/*.* pi@192.168.2.81:/home/pi/hem/
scp -r ~/Smarthome/hem/site/* pi@192.168.2.81:/home/pi/hem/site/
scp ~/Smarthome/hem/init.d/hem pi@192.168.2.81:/etc/init.d/hem 

