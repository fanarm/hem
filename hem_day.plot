set terminal png size 1200,500
# set terminal png size wide,height
set xdata time
set timefmt "%H:%M:%S"
set format x "%H"
# time range must be in same format as data file
set xrange ["00:00":"23:59"]
set datafile sep whitespace
set output "/home/pi/hem/pic/hem_`date +%Y_%m_%d`.png"
#set yrange autoscale
set grid
set xlabel "Time of day"
set ylabel "\nPM2.5, Temp and Humidity"
set title "PM2.5, Temperature and Humidity over time on `date +%b.%d,%A,%Y`"
set key autotitle columnhead
set key right box
#set linetype 1 lw 1 lc rgb "green"
#set linetype 2 lw 1 lc rgb "orange"
#set linetype 3 lw 1 lc rgb "blue"
plot for [col=3:5] "/home/pi/hem/log/pmth_plot_`date +%Y_%m_%d`.log" using 2:col with lines
#plot "`date +%d-%b-%Y`.txt" using 1:2 index 0 title "SoC" with lines, "/home/pi/AmbientTemp/`date +%d-%b-%Y`.txt" using 1:2 title "Ambient" with lines, "limit.txt" using 1:2 title "58.6c safe limit" with lines
