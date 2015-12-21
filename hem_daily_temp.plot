set terminal png linewidth 4 font arial 28 size 700,500
# set terminal png size wide,height
set xdata time
set timefmt "%H:%M:%S"
set format x "%H"
# time range must be in same format as data file
set xrange ["00:00":"23:59"]
set xtics "00:00","4:00","23:59"
set datafile sep whitespace
set output "/home/pi/hem/pic/hem_temp_`date +%Y_%m_%d`.png"
set yrange [*<0:30<*]
set grid
set xlabel "Time of day"
set ylabel "Temperature(ºC)"
set title "Temp. over time on `date +%b.%d,%a`"
set key off
set linetype 1 lw 1 lc rgb "orange"
plot "/home/pi/hem/log/pmth_plot_`date +%Y_%m_%d`.log" using 2:4 with lines
