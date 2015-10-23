import os
import string
import datetime
import time
import random
import matplotlib.pyplot as plt
from matplotlib import dates
import argparse

from scipy import integrate
import numpy as np
import matplotlib.pyplot as plt

DEST="../output/"
DEST_SELECTED="../output-selected"
TIMESTAMP = time.strftime("%Y%m%d-%H%M%S")
DIR=DEST+TIMESTAMP
if not os.path.exists(DIR):
    os.makedirs(DIR)
META=DIR+"/meta.txt"
OUT=DIR+"/output.txt"

def meta_record(items):
  # Meant to be called once at the beginning of the program to save metadata about the run to META file
  try:
    f = open(META, 'w')
  except IOError:
    print 'Cannon open', META
    exit(1)
  else:
    for i in items:
      f.write(str(i)+"\n")
    f.close() 

def out_record(s):
  # Meant to be run many times through the code to save intermediate results to OUT file
  print s
  try:
    f = open(OUT, 'a')
  except IOError:
    print 'Cannon open', OUT
    exit(1)
  else:
    f.write(str(s)+"\n")
    f.close()

def load(filename):
  try:
    f = open(filename, 'r')
  except IOError:
    print 'Cannot open ', filename
    exit(1)
  else:
    lines=[]
    for l in f:
      lines.append(l)
    f.close()
    return lines

def CM_process(raw):
  res = []
  t_min = float('Inf')
  t_max = -float('Inf')
  # Timestamps in CM samples has this format: 2015-07-01 14:00:52.61
  # Timestamps use UTC timestamps and are processed here accordingly
  pattern = '%Y-%m-%d %H:%M:%S.%f'
  for i in raw:
    x=i.split(",")
    t=x[1]
    epoch=(datetime.datetime.strptime(t,pattern)-datetime.datetime.utcfromtimestamp(0)).total_seconds()
    t_min=min(t_min,epoch)
    t_max=max(t_max,epoch)
    p=float(x[2].rstrip())
    res.append( (epoch,p) )
  # res will contain records like this:
  #   (1443886995.596, 39.0)
  #   (1443887074.264, 40.0)
  #   ...
  return (res, t_min, t_max)

def NO_process_full(raw):
  # Find the first voltage
  volt = 0
  for s in raw:
    x=s.split(",")
    cmd=x[3]
    if cmd=="VIN":
      volt = float(x[5])
      break 
  # Calculated power estimates
  t_min = float('Inf')
  t_max = -float('Inf')
  res = []
  for s in raw:
    x=s.split(",")
    cmd=x[3]
    if cmd=="VIN":
      volt = float(x[5]) 
    elif cmd == "IOUT":
      epoch=float(x[0])
      t_min=min(t_min,epoch)
      t_max=max(t_max,epoch)
      curr = float(x[5])
      p = curr * volt;
      res.append(s.rstrip() + "," + str(volt) + "," + str(p))
  # res will contain records like this:
  #   1443894438.04,2015-10-03 17:47:18.043701,ms0128.utah.cloudlab.us,IOUT,rcvd: 52 00 08 09,3.27398,12.327336,40.3594515173
  #   1443894440.28,2015-10-03 17:47:20.283455,ms0128.utah.cloudlab.us,IOUT,rcvd: 52 00 08 09,3.27398,12.327336,40.3594515173
  #   ...
  # Last three columns: current, voltage, power
  return (res, t_min, t_max)

def NO_process(raw):
  full,t_min,t_max=NO_process_full(raw)
  res = []
  for s in full:
    x = s.split(",")
    res.append( (float(x[0]),float(x[7])) )  
  # res will contain records like this:
  #   (1443904933.73, 40.5121872103)
  #   (1443904936.02, 40.3594515173)
  return (res,t_min,t_max)

def split_samples(samples,start,end):
  t = []
  p = []

  # Old way: Connect all measurements
  ## for s in samples:
  ##  # Choose samples that fall in the overlapping interval
  ##  if (s[0] >= start) and (s[0] <= end):
  ##    t.append(s[0])
  ##    p.append(s[1])

  # New way: Rectangles - propagate current value until the new value is recorded
  for i in range(0,len(samples)-1):
    if (samples[i][0] >= start) and (samples[i][0] <= end):  
      t.append(samples[i][0])
      p.append(samples[i][1])
      t.append(samples[i+1][0])
      p.append(samples[i][1])
  return (t,p)

def convert_time_vector(tv):
  # Convert epoch time samples to appropriate format for plotting
  return dates.date2num(map(datetime.datetime.fromtimestamp, tv))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cm', help="File with CM samples")
    parser.add_argument('--node', help="File with on-node samples")
    parser.add_argument("--select_overlap", help="Select an interval of overlapping samples", action="store_true")
    parser.add_argument("--start", help="Number between 0 and 100, which defines the start of the subinterval which will be selected", default=0)
    parser.add_argument("--end", help="Number between 0 and 100, which defines the end of the subinterval which will be selected", default=100)
    parser.add_argument("--no_display", help="Do not show the graph; Useful for batch processing", action="store_true")
    args = parser.parse_args()
    
    # Save metadata into a file  
    meta_record([parser, args, "\n\nProcessing script:\n", string.join(load(parser.prog))])
   
    # Get contents of the input files 
    cmpow_raw = load(args.cm)
    nopow_raw = load(args.node)
  
    # ----------------
    # Begin processing
    cmpow,cm_t_min,cm_t_max = CM_process(cmpow_raw)    
    nopow,no_t_min,no_t_max = NO_process(nopow_raw)
    out_record("Processed CM data: " + str(len(cmpow)) + " power samples")
    out_record("Processed NO data: " + str(len(nopow)) + " power samples")

    if args.select_overlap: 
      overlap_start = max(cm_t_min,no_t_min)
      overlap_end = min(cm_t_max,no_t_max)
    else:
      # These values effectively disable selection
      overlap_start=min(cm_t_min,no_t_min)
      overlap_end=max(cm_t_max,no_t_max)

    # Apply start_percent and end_percent to select specific subinterval
    overlap_len = overlap_end - overlap_start
    start = overlap_start + overlap_len * float(args.start)/100.0
    end = overlap_start + overlap_len * float(args.end)/100.0
    out_record("Start of selection interval (epoch): " + str(start))
    out_record("End of selection interval (epoch): "+ str(end))
    out_record("Length of selection interval: " + str(end - start) + " seconds")

    # Splitting 
    cm_t_epoch,cm_p = split_samples(cmpow,start,end)
    no_t_epoch,no_p = split_samples(nopow,start,end)

    # TEST: CONSTANT POWER
    #for i in range(0,len(cm_p)):
    #  cm_p[i]= 47.0
    #for i in range(0,len(no_p)):
    #  no_p[i]= 15.0
	# END OF TEST

    # Cumulative numerical integration using trapezoid rule
    # For correct integration, it is important to use epoch times (which are in seconds)
    cm_pow_int = integrate.cumtrapz(cm_p, cm_t_epoch, initial=0)
    no_pow_int = integrate.cumtrapz(no_p, no_t_epoch, initial=0)
    
    # Find relative difference in cumulative power at the end of the interval
    p1=cm_pow_int[len(cm_pow_int)-1]
    p2=no_pow_int[len(no_pow_int)-1]
    rel_dif = abs(p1-p2)/min(p1,p2) * 100.0
    out_record("Difference in cumulative power at the end of the selected interval: " + str(rel_dif) + "%")
    
    # Covert cumulative power from J to kJ
    for i in range(0,len(cm_pow_int)):
      cm_pow_int[i]= cm_pow_int[i]/1000.0
    for i in range(0,len(no_pow_int)):
      no_pow_int[i]= no_pow_int[i]/1000.0

    # Time conversion
    cm_t = convert_time_vector(cm_t_epoch)
    no_t = convert_time_vector(no_t_epoch)

    


    # Plotting:
    print "Creating a graph and displyaing it..."
    fig = plt.figure()
    plt.ylabel('Instantaneous Power Draw, Watt')
    plt.title('Comparison of Power Measurements on CloudLab\'s ARM nodes')
    plt.xticks(rotation=45)
    ## Optional: beautify the x-labels
    #plt.gcf().autofmt_xdate()
    plt.subplots_adjust(bottom=.3)

    ax1 = fig.add_subplot(111)
    ax1.plot(no_t, no_p, label="On-node Measurements - "+ str(len(no_p)) + " samples")
    ax1.plot(cm_t, cm_p, label="CM Measurements - " + str(len(cm_p)) + " samples")
    
    ax1.xaxis.set_major_locator(dates.AutoDateLocator())
    ax1.xaxis.set_major_formatter(dates.DateFormatter('%m/%d %H:%M:%S'))
    ax1.set_ylim(bottom = 0)

    ax2 = ax1.twinx()
    ax2.plot(no_t, no_pow_int, '--', label="On-node cumulative power")
    ax2.plot(cm_t, cm_pow_int, '-.', label="CM cumulative power")
    ax2.set_ylabel('Cumulative Power, kJ')
    
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    # loc=4 - lower right corner
    ax1.legend(h1+h2, l1+l2, loc=4)
    if not(args.no_display): 
      plt.show()
    fig.savefig(DIR + "/power.png") 
    plt.close(fig) 

    # -------------
    # Final output to the console
    print "Processing is complete. See output in: " + DIR
    print "Created files:"
    for f in os.listdir(DIR):
      print(os.path.join(DIR, f))
    print "To preserve the results, run: cp -r " + DIR + " " + DEST_SELECTED
