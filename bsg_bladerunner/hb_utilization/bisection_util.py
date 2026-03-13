#
#   bisection_util.py
#
#   this script reports bisection bandwidth utilization;
#

import sys
import pandas as pd

def convert_dir(d):
  if d == 0:
    return "P"
  elif d == 1:
    return "W"
  elif d == 2:
    return "E"
  elif d == 3:
    return "N"
  elif d == 4:
    return "S"
  elif d == 5:
    return "RW"
  elif d == 6:
    return "RE"
  else:
    return "X"


class BisectionBW:
  # constructor;
  def __init__(self, csvpath, rf_x, num_tiles_x, num_tiles_y, num_pods_x):
    # path to router_stat.csv;
    self.csvpath = csvpath

    # ruche factor;
    self.rf_x = rf_x

    # dim;
    self.num_tiles_x = num_tiles_x
    self.num_tiles_y = num_tiles_y
    self.num_pods_x = num_pods_x
    return
    

  # parse helper;
  def parse(self):
    # parse csv to df;
    df = pd.read_csv(self.csvpath)
 
    # find start and end timestamp   
    timestamps = df["global_ctr"]
    start_timestamp = (2**32)-1
    end_timestamp = 0
    for i in range(len(timestamps)):
      timestamp = timestamps[i]
      if start_timestamp > timestamp:
        start_timestamp = timestamp
      if end_timestamp < timestamp:
        end_timestamp = timestamp

    # total cycle
    total_cycle = float(end_timestamp - start_timestamp)

    # modify xy and dir;
    df["x"] = df["x"].subtract(self.num_tiles_x)
    df["y"] = df["y"].subtract(self.num_tiles_y)
    df["output_dir"] = df.apply(lambda x: convert_dir(x.output_dir), axis = 1)
    # filter rows; 
    df = df[(df["x"] >= 0) & (df["x"] < self.num_tiles_x*self.num_pods_x)]
    df = df[(df["y"] >= 0) & (df["y"] < self.num_tiles_y)]
    # separate out start and end;
    fwd_start_df = df[(df["global_ctr"]==start_timestamp) & (df["XY_order"] == 1)]
    fwd_end_df   = df[(df["global_ctr"]==end_timestamp) & (df["XY_order"] == 1)]


    # horizontal bisection; (fwd)
    fwd_hor_idle        = 0
    fwd_hor_utilized    = 0
    fwd_hor_stalled     = 0
    for px in range(self.num_pods_x):
      x_left = (self.num_tiles_x*px)+(self.num_tiles_x/2)-1
      x_right = (self.num_tiles_x*px)+(self.num_tiles_x/2)
      # end
      temp_df = fwd_end_df[(fwd_end_df["output_dir"] == "E") & (fwd_end_df["x"] == x_left)]
      fwd_hor_idle        += sum(temp_df["idle"])
      fwd_hor_utilized    += sum(temp_df["utilized"])
      fwd_hor_stalled     += sum(temp_df["stalled"])
      temp_df = fwd_end_df[(fwd_end_df["output_dir"] == "W") & (fwd_end_df["x"] == x_right)]
      fwd_hor_idle        += sum(temp_df["idle"])
      fwd_hor_utilized    += sum(temp_df["utilized"])
      fwd_hor_stalled     += sum(temp_df["stalled"])
      for rf in range(self.rf_x):
        temp_df = fwd_end_df[(fwd_end_df["output_dir"] == "RE") & (fwd_end_df["x"] == x_left-rf)]
        fwd_hor_idle        += sum(temp_df["idle"])
        fwd_hor_utilized    += sum(temp_df["utilized"])
        fwd_hor_stalled     += sum(temp_df["stalled"])
        temp_df = fwd_end_df[(fwd_end_df["output_dir"] == "RW") & (fwd_end_df["x"] == x_right+rf)]
        fwd_hor_idle        += sum(temp_df["idle"])
        fwd_hor_utilized    += sum(temp_df["utilized"])
        fwd_hor_stalled     += sum(temp_df["stalled"])
      # start
      temp_df = fwd_start_df[(fwd_start_df["output_dir"] == "E") & (fwd_start_df["x"] == x_left)]
      fwd_hor_idle        -= sum(temp_df["idle"])
      fwd_hor_utilized    -= sum(temp_df["utilized"])
      fwd_hor_stalled     -= sum(temp_df["stalled"])
      temp_df = fwd_start_df[(fwd_start_df["output_dir"] == "W") & (fwd_start_df["x"] == x_right)]
      fwd_hor_idle        -= sum(temp_df["idle"])
      fwd_hor_utilized    -= sum(temp_df["utilized"])
      fwd_hor_stalled     -= sum(temp_df["stalled"])
      for rf in range(self.rf_x):
        temp_df = fwd_start_df[(fwd_start_df["output_dir"] == "RE") & (fwd_start_df["x"] == x_left-rf)]
        fwd_hor_idle        -= sum(temp_df["idle"])
        fwd_hor_utilized    -= sum(temp_df["utilized"])
        fwd_hor_stalled     -= sum(temp_df["stalled"])
        temp_df = fwd_start_df[(fwd_start_df["output_dir"] == "RW") & (fwd_start_df["x"] == x_right+rf)]
        fwd_hor_idle        -= sum(temp_df["idle"])
        fwd_hor_utilized    -= sum(temp_df["utilized"])
        fwd_hor_stalled     -= sum(temp_df["stalled"])
  
    # divide by total cycle       
    fwd_hor_idle        /= (2*(1+self.rf_x)*self.num_tiles_y*total_cycle*self.num_pods_x)
    fwd_hor_utilized    /= (2*(1+self.rf_x)*self.num_tiles_y*total_cycle*self.num_pods_x)
    fwd_hor_stalled     /= (2*(1+self.rf_x)*self.num_tiles_y*total_cycle*self.num_pods_x)
    fwd_hor_idle *= 100
    fwd_hor_utilized *= 100
    fwd_hor_stalled *= 100
    
    stat = {}
    stat["utilized"] = fwd_hor_utilized
    stat["idle"]     = fwd_hor_idle
    stat["stalled"]  = fwd_hor_stalled
    return stat

  def summarize_stat(self, stat):
    print("utilized: {:.2f}".format(stat["utilized"]))
    print("idle:     {:.2f}".format(stat["idle"]))
    print("stalled:  {:.2f}".format(stat["stalled"]))
    return



# main function;
if __name__ == "__main__":
  # arguments;
  csvpath = sys.argv[1] + "router_stat.csv"
  rf_x = int(sys.argv[2])
  num_tiles_x = int(sys.argv[3])
  num_tiles_y = int(sys.argv[4])
  num_pods_x = int(sys.argv[5])

  bw = BisectionBW(csvpath, rf_x, num_tiles_x, num_tiles_y, num_pods_x)
  stat = bw.parse()
  bw.summarize_stat(stat)
