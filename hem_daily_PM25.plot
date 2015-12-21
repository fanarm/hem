set terminal png linewidth 4 font arial 28 size 1400,600
# set terminal png size wide,height
set xdata time
set timefmt "%H:%M:%S"
set format x "%H"
# time range must be in same format as data file
set xrange ["00:00":"23:59"]
set datafile sep whitespace
set output "/home/pi/hem/pic/hem_pm25_`date +%Y_%m_%d`.png"
set yrange [0:50<*]
set grid
set xlabel "Time of day"
set ylabel "\nPM2.5"
set title "PM2.5 over time on `date +%b.%d,%A,%Y`"
set key off
set linetype 1 lw 1 lc rgb "green"
plot "/home/pi/hem/log/pmth_plot_`date +%Y_%m_%d`.log" using 2:3 with lines
