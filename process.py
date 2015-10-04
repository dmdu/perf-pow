import datetime
import time
import random
import matplotlib.pyplot as plt
from matplotlib import dates

ddir="../log/hpgmg-fe_arm_core_scaling"
node_measurement_fname=ddir+"/ms0128.utah.cloudlab.us.log"
chassis_measurement_fname=ddir+"/504.csv"

# Gap threshold, seconds
gapt=10

def loader(filename):
  f=open(filename, "r")
  l=[]
  for line in f:
    l.append(line)
  f.close()
  return l

l = loader(node_measurement_fname)
u_raw = loader(chassis_measurement_fname)

u = []
# Example from UMass: 2015-07-01 14:00:52.61
pattern = '%Y-%m-%d %H:%M:%S.%f'
for i in u_raw:
  x=i.split(",")
  t=x[1]
  p=float(x[2].rstrip())
  #epoch = int(time.mktime(time.strptime(t, pattern)))
  epoch=(datetime.datetime.strptime(t,pattern)-datetime.datetime.utcfromtimestamp(0)).total_seconds()
  u.append((epoch,p)) 
#print u

# find intervals
invs =[]
last = 0
for i in range(0,len(l)-1):
  tnow = ((l[i]).split(","))[0]
  tnext = ((l[i+1]).split(","))[0]
  #print tnow, tnext
  # large gap 
  if float(tnext) - float(tnow) >= gapt:
    invs.append( (last,i) )
    last = i+1

if not invs:
	invs.append( (0,len(l)-1) )

#crop
invs.append( (6500,8800) )

print invs

# process selected interval
for sint in range(0,len(invs)):
  print "interval: " + str(sint) 	
  chunk = l[invs[sint][0]:invs[sint][1]+1]
  
  # find initial voltageo
  volt = 0
  for i in range(0,len(chunk)):
    x=(chunk[i]).split(",")
    cmd=x[3]
    if cmd=="VIN":
      volt = float(x[5])
      break;  
  #print chunk
  #print volt 
  
  # calculated power estimates
  powm = []
  for i in range(0,len(chunk)):
    x=(chunk[i]).split(",")
    cmd=x[3]
    if cmd=="VIN":
      volt = float(x[5])  
      #print volt
    elif cmd == "IOUT":
      curr = float(x[5]) 
      p = curr * volt;
      powm.append(chunk[i].rstrip() + "," + str(volt) + "," + str(p))
  
  #for i in range(0,len(powm)):
  #  print powm[i]
  
  # prepare lists for graphing
  xval = []
  yval = []
  for i in range(0,len(powm)):
    x=(powm[i]).split(",")
    xval.append(float(x[0]))
    yval.append(float(x[7]))
  
  # find overlapping Umass chunk
  uchunk = []
  lb=min(xval)
  ub=max(xval)
  #print lb, ub
  start = 0
  end = len(u)-1
  for i in range(0,len(u)-1):
    if u[i][0] < lb and u[i+1][0] > lb:
      start = i
    if u[i][0] < ub and u[i+1][0] > ub:
  	end = i+1
  #print 0,len(u)-1
  #print start, end
  uoverlap=u[start:end+1]
  #print uoverlap
  uoverlapx = []
  uoverlapy = []
  
  urawoverlap=u_raw[start:end+1]
  for el in  urawoverlap:
	  print el.rstrip()
  print "end of raw"

  for el in uoverlap:
    uoverlapx.append(el[0])
    uoverlapy.append(el[1])

  
  
  # time converstion
  tt = map(datetime.datetime.fromtimestamp, xval)
  #print tt
  fds = dates.date2num(tt)
  #print fds
  
  ttu = map(datetime.datetime.fromtimestamp, uoverlapx)
  fdsu = dates.date2num(ttu)
  #print fdsu

  for i in range(0, len(uoverlapy)):
	  print fdsu[i], ", ", uoverlapy[i]
  
  
  hfmt = dates.DateFormatter('%m/%d %H:%M:%S')
  
  # graphing:
  fig = plt.figure()
  ax = fig.add_subplot(111)
  ax.plot(fds, yval, label="On-node Measurements - "+ str(len(yval)) + " samples")
  ax.plot(fdsu, uoverlapy, label="CM Measurements - " + str(len(uoverlapy)) + " samples")
  plt.ylabel('Instantaneous Power Draw, Watt')
  plt.title('Comparison of Power Measurements on CloudLab\'s ARM nodes')
  plt.legend(loc="best")
  
  ax.xaxis.set_major_locator(dates.AutoDateLocator())
  ax.xaxis.set_major_formatter(hfmt)
  ax.set_ylim(bottom = 0)
  plt.xticks(rotation=45)
  plt.subplots_adjust(bottom=.3)
  #plt.show()
  fig.savefig(ddir + "/" + str(sint) + '.png') 
  plt.close(fig) 
  
