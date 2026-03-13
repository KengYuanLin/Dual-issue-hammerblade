#
#   remote_load_stat.py
#
#   python remote_load_stat.py {ruche_x} {depop} {csvpath}
#

import csv
import sys
import os
from statistics import mean


def mesh_delay(dx, dy):
  return (dx+dy)*2 


def ruche_pop_delay(rf_x, dx, dy):
  delay_x = 0
  curr_x = dx
    
  while curr_x > 0:
    if curr_x >= rf_x:
      curr_x -= rf_x
      delay_x += 1
    else:
      curr_x -= 1
      delay_x +=1

  return (2*dy)+ (2*delay_x)


def ruche_depop_delay(rf_x, dx, dy):
  delay_x = 0
  curr_x = dx
    
  while curr_x > 0:
    if curr_x > rf_x:
      curr_x -= rf_x
      delay_x += 1
    else:
      curr_x -= 1
      delay_x +=1

  return (2*dy) + (2*delay_x)

def parse_remote_load_stat(rf_x, depop, filename="remote_load_trace.csv"):
  # parse csv;
  try: 
    f = open(filename, "r")
  except:
    print("{} not found.".format(filename))
    return
  csv_reader = csv.DictReader(f, delimiter=",")
 
  int_delays = []
  con_delays = []
  total_delays  = []
  
  for row in csv_reader:
    src_x = int(row["src_x"]) 
    src_y = int(row["src_y"]) 
    dest_x = int(row["dest_x"]) 
    dest_y = int(row["dest_y"]) 
    dx = abs(src_x-dest_x)
    dy = abs(src_y-dest_y)
    latency = int(row["latency"])

    # calculate intrinsic delay;
    int_delay = 3
    if rf_x  == 0:
      int_delay += mesh_delay(dx,dy)
    else:
      if depop == 0:
        int_delay += ruche_pop_delay(rf_x,dx,dy)
      else:
        int_delay += ruche_depop_delay(rf_x,dx,dy)
    # congestion delay
    con_delay = latency - int_delay
    assert con_delay >= 0, "latency = {}, int_delay = {}, con_delay = {}, dx = {}, dy = {}".format(latency, int_delay, con_delay, dx, dy)

    total_delays.append(latency)
    int_delays.append(int_delay)
    con_delays.append(con_delay)


  # average;
  int_mean = mean(int_delays)
  con_mean = mean(con_delays)
  total_mean = mean(total_delays)
  
  #print("mean total      delay = {}".format(total_mean))
  print("mean intrinsic  delay = {:.2f}".format(int_mean))
  print("mean congestion delay = {:.2f}".format(con_mean))

# main
if __name__ == "__main__":
  rf_x = int(sys.argv[1])
  depop = int(sys.argv[2])
  os.chdir(sys.argv[3])
  parse_remote_load_stat(rf_x, depop)
