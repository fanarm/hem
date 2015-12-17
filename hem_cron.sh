#!/bin/bash
date >> /home/pi/hem/pic/hem_day_plot.log
gnuplot /home/pi/hem/hem_day.plot >> /home/pi/hem/pic/hem_day_plot.log
