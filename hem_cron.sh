#!/bin/bash
date >> /home/pi/hem/pic/hem_day_plot.log
gnuplot /home/pi/hem/hem_daily_PM25.plot >> /home/pi/hem/pic/hem_day_plot.log
gnuplot /home/pi/hem/hem_daily_temp.plot >> /home/pi/hem/pic/hem_day_plot.log
gnuplot /home/pi/hem/hem_daily_humid.plot >> /home/pi/hem/pic/hem_day_plot.log
