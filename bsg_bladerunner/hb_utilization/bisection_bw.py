#
#   bisection_bw.py
#
#   python bisection_bw.py {path_to_hammerbench_hb} {rf_x}

import sys
import pandas as pd

POD_ORIGIN_X=16
POD_ORIGIN_Y=8
NUM_TILES_X=16
NUM_TILES_Y=8

BENCHMARK_PATHS = {
  "AES"       : "apps/aes/opt-pod",
  "SW"        : "apps/smith_waterman",
  "BS"        : "apps/blackscholes/opt-pod",
  "SGEMM"     : "apps/gemm/sgemm_512/tile-x_16__tile-y_8",
  "FFT"       : "apps/fft/256/tile-x_16__tile-y_8__num-iter_2__warm-cache_no",
  "Jacobi"    : "apps/jacobi/nx_32__ny_16__nz_512__num-iter_1__warm-cache_no",
  "BH"        : "apps/barnes_hut",
  "Pagerank"  : "apps/pagerank/direction_pull__fn_pagerank_pull_u8__graph_wiki-Vote__pod-id_0__npods_1",
  "BFS"       : "apps/bfs-single-pod/input_g16k16__start_61526__opt-fwd-ilp-inner_1__opt-mu-ilp-inner_2__opt-rev-pre-outer_4",
  "SpGEMM"    : "apps/spgemm/spmm_abrev_multi_pod_model/u12k2_input__1_partfactor__0x0_partition__yes_opt__yes_parallel",
  "memcpy"    : "apps/memcpy/tile-x_16__tile-y_8__buffer-size_524288__warm-cache_no",
  "gups_vcache"  : "apps/gups_rmw/tile-x_16__tile-y_8__A-size_1024__warm-cache_yes",
  "gups_dram"    : "apps/gups_rmw/tile-x_16__tile-y_8__A-size_67108864__warm-cache_no",
}

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
  def __init__(self, hbench_path, rf_x):
    # hammerbench path
    self.hbench_path = hbench_path

    # rf
    self.rf_x = rf_x
  
    # output df;
    df_cols = ["Network", "Direction", "Stat"] + list(BENCHMARK_PATHS.keys())
    self.fwd_output_df = pd.DataFrame(columns=df_cols)
    df_cols = ["Network", "Direction", "Stat"] + list(BENCHMARK_PATHS.keys())
    self.rev_output_df = pd.DataFrame(columns=df_cols)

    # vertical  bisection;
    self.fwd_ver_idle       = []
    self.fwd_ver_utilized   = []
    self.fwd_ver_stalled    = []
    self.rev_ver_idle       = []
    self.rev_ver_utilized   = []
    self.rev_ver_stalled    = []
    
    # horizontal bisection
    self.fwd_hor_idle       = []
    self.fwd_hor_utilized   = []
    self.fwd_hor_stalled    = []
    self.rev_hor_idle       = []
    self.rev_hor_utilized   = []
    self.rev_hor_stalled    = []
    return
    

  # parse router_stat.csv;
  def parse(self):
    for key in BENCHMARK_PATHS.keys():
      print(key)
      self.parse_helper(key)
    return


  # parse helper;
  def parse_helper(self, bname):
    # parse csv to df;
    csv_path = self.hbench_path + "/" + BENCHMARK_PATHS[bname] + "/router_stat.csv"
    df = pd.read_csv(csv_path)
 
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
    df["x"] = df["x"].subtract(POD_ORIGIN_X)
    df["y"] = df["y"].subtract(POD_ORIGIN_Y)
    df["output_dir"] = df.apply(lambda x: convert_dir(x.output_dir), axis = 1)

    # filter rows; 
    df = df[(df["x"] >= 0) & (df["x"] < NUM_TILES_X)]
    df = df[(df["y"] >= 0) & (df["y"] < NUM_TILES_Y)]

    # separate out start and end;
    fwd_start_df = df[(df["global_ctr"]==start_timestamp) & (df["XY_order"] == 1)]
    fwd_end_df   = df[(df["global_ctr"]==end_timestamp) & (df["XY_order"] == 1)]
    rev_start_df = df[(df["global_ctr"]==start_timestamp) & (df["XY_order"] == 0)]
    rev_end_df   = df[(df["global_ctr"]==end_timestamp) & (df["XY_order"] == 0)]

    # vertical bisection; (fwd)
    fwd_ver_idle        = 0
    fwd_ver_utilized    = 0
    fwd_ver_stalled     = 0
    # end
    temp_df = fwd_end_df[(fwd_end_df["output_dir"] == "S") & (fwd_end_df["y"] == 3)]
    fwd_ver_idle        += sum(temp_df["idle"])
    fwd_ver_utilized    += sum(temp_df["utilized"])
    fwd_ver_stalled     += sum(temp_df["stalled"])
    temp_df = fwd_end_df[(fwd_end_df["output_dir"] == "N") & (fwd_end_df["y"] == 4)]
    fwd_ver_idle        += sum(temp_df["idle"])
    fwd_ver_utilized    += sum(temp_df["utilized"])
    fwd_ver_stalled     += sum(temp_df["stalled"])
    # start
    temp_df = fwd_start_df[(fwd_start_df["output_dir"] == "S") & (fwd_start_df["y"] == 3)]
    fwd_ver_idle        -= sum(temp_df["idle"])
    fwd_ver_utilized    -= sum(temp_df["utilized"])
    fwd_ver_stalled     -= sum(temp_df["stalled"])
    temp_df = fwd_start_df[(fwd_start_df["output_dir"] == "N") & (fwd_start_df["y"] == 4)]
    fwd_ver_idle        -= sum(temp_df["idle"])
    fwd_ver_utilized    -= sum(temp_df["utilized"])
    fwd_ver_stalled     -= sum(temp_df["stalled"])
    
    fwd_ver_idle        /= (2*NUM_TILES_X*total_cycle)
    fwd_ver_utilized    /= (2*NUM_TILES_X*total_cycle)
    fwd_ver_stalled     /= (2*NUM_TILES_X*total_cycle)

    self.fwd_ver_idle.append(fwd_ver_idle)
    self.fwd_ver_utilized.append(fwd_ver_utilized)
    self.fwd_ver_stalled.append(fwd_ver_stalled)

    # vertical bisection; (rev)
    rev_ver_idle        = 0
    rev_ver_utilized    = 0
    rev_ver_stalled     = 0
    # end
    temp_df = rev_end_df[(rev_end_df["output_dir"] == "S") & (rev_end_df["y"] == 3)]
    rev_ver_idle        += sum(temp_df["idle"])
    rev_ver_utilized    += sum(temp_df["utilized"])
    rev_ver_stalled     += sum(temp_df["stalled"])
    temp_df = rev_end_df[(rev_end_df["output_dir"] == "N") & (rev_end_df["y"] == 4)]
    rev_ver_idle        += sum(temp_df["idle"])
    rev_ver_utilized    += sum(temp_df["utilized"])
    rev_ver_stalled     += sum(temp_df["stalled"])
    # start
    temp_df = rev_start_df[(rev_start_df["output_dir"] == "S") & (rev_start_df["y"] == 3)]
    rev_ver_idle        -= sum(temp_df["idle"])
    rev_ver_utilized    -= sum(temp_df["utilized"])
    rev_ver_stalled     -= sum(temp_df["stalled"])
    temp_df = rev_start_df[(rev_start_df["output_dir"] == "N") & (rev_start_df["y"] == 4)]
    rev_ver_idle        -= sum(temp_df["idle"])
    rev_ver_utilized    -= sum(temp_df["utilized"])
    rev_ver_stalled     -= sum(temp_df["stalled"])
    
    rev_ver_idle        /= (2*NUM_TILES_X*total_cycle)
    rev_ver_utilized    /= (2*NUM_TILES_X*total_cycle)
    rev_ver_stalled     /= (2*NUM_TILES_X*total_cycle)

    self.rev_ver_idle.append(rev_ver_idle)
    self.rev_ver_utilized.append(rev_ver_utilized)
    self.rev_ver_stalled.append(rev_ver_stalled)


    # horizontal bisection; (fwd)
    fwd_hor_idle        = 0
    fwd_hor_utilized    = 0
    fwd_hor_stalled     = 0
    # end
    temp_df = fwd_end_df[(fwd_end_df["output_dir"] == "E") & (fwd_end_df["x"] == 7)]
    fwd_hor_idle        += sum(temp_df["idle"])
    fwd_hor_utilized    += sum(temp_df["utilized"])
    fwd_hor_stalled     += sum(temp_df["stalled"])
    temp_df = fwd_end_df[(fwd_end_df["output_dir"] == "W") & (fwd_end_df["x"] == 8)]
    fwd_hor_idle        += sum(temp_df["idle"])
    fwd_hor_utilized    += sum(temp_df["utilized"])
    fwd_hor_stalled     += sum(temp_df["stalled"])
    for rf in range(self.rf_x):
      temp_df = fwd_end_df[(fwd_end_df["output_dir"] == "RE") & (fwd_end_df["x"] == 7-rf)]
      fwd_hor_idle        += sum(temp_df["idle"])
      fwd_hor_utilized    += sum(temp_df["utilized"])
      fwd_hor_stalled     += sum(temp_df["stalled"])
      temp_df = fwd_end_df[(fwd_end_df["output_dir"] == "RW") & (fwd_end_df["x"] == 8+rf)]
      fwd_hor_idle        += sum(temp_df["idle"])
      fwd_hor_utilized    += sum(temp_df["utilized"])
      fwd_hor_stalled     += sum(temp_df["stalled"])
    # start
    temp_df = fwd_start_df[(fwd_start_df["output_dir"] == "E") & (fwd_start_df["x"] == 7)]
    fwd_hor_idle        -= sum(temp_df["idle"])
    fwd_hor_utilized    -= sum(temp_df["utilized"])
    fwd_hor_stalled     -= sum(temp_df["stalled"])
    temp_df = fwd_start_df[(fwd_start_df["output_dir"] == "W") & (fwd_start_df["x"] == 8)]
    fwd_hor_idle        -= sum(temp_df["idle"])
    fwd_hor_utilized    -= sum(temp_df["utilized"])
    fwd_hor_stalled     -= sum(temp_df["stalled"])
    for rf in range(self.rf_x):
      temp_df = fwd_start_df[(fwd_start_df["output_dir"] == "RE") & (fwd_start_df["x"] == 7-rf)]
      fwd_hor_idle        -= sum(temp_df["idle"])
      fwd_hor_utilized    -= sum(temp_df["utilized"])
      fwd_hor_stalled     -= sum(temp_df["stalled"])
      temp_df = fwd_start_df[(fwd_start_df["output_dir"] == "RW") & (fwd_start_df["x"] == 8+rf)]
      fwd_hor_idle        -= sum(temp_df["idle"])
      fwd_hor_utilized    -= sum(temp_df["utilized"])
      fwd_hor_stalled     -= sum(temp_df["stalled"])
         
    fwd_hor_idle        /= (2*(1+self.rf_x)*NUM_TILES_Y*total_cycle)
    fwd_hor_utilized    /= (2*(1+self.rf_x)*NUM_TILES_Y*total_cycle)
    fwd_hor_stalled     /= (2*(1+self.rf_x)*NUM_TILES_Y*total_cycle)

    self.fwd_hor_idle.append(fwd_hor_idle)
    self.fwd_hor_utilized.append(fwd_hor_utilized)
    self.fwd_hor_stalled.append(fwd_hor_stalled)


    # horizontal bisection; (rev)
    rev_hor_idle        = 0
    rev_hor_utilized    = 0
    rev_hor_stalled     = 0
    # end
    temp_df = rev_end_df[(rev_end_df["output_dir"] == "E") & (rev_end_df["x"] == 7)]
    rev_hor_idle        += sum(temp_df["idle"])
    rev_hor_utilized    += sum(temp_df["utilized"])
    rev_hor_stalled     += sum(temp_df["stalled"])
    temp_df = rev_end_df[(rev_end_df["output_dir"] == "W") & (rev_end_df["x"] == 8)]
    rev_hor_idle        += sum(temp_df["idle"])
    rev_hor_utilized    += sum(temp_df["utilized"])
    rev_hor_stalled     += sum(temp_df["stalled"])
    for rf in range(self.rf_x):
      temp_df = rev_end_df[(rev_end_df["output_dir"] == "RE") & (rev_end_df["x"] == 7-rf)]
      rev_hor_idle        += sum(temp_df["idle"])
      rev_hor_utilized    += sum(temp_df["utilized"])
      rev_hor_stalled     += sum(temp_df["stalled"])
      temp_df = rev_end_df[(rev_end_df["output_dir"] == "RW") & (rev_end_df["x"] == 8+rf)]
      rev_hor_idle        += sum(temp_df["idle"])
      rev_hor_utilized    += sum(temp_df["utilized"])
      rev_hor_stalled     += sum(temp_df["stalled"])
    # start
    temp_df = rev_start_df[(rev_start_df["output_dir"] == "E") & (rev_start_df["x"] == 7)]
    rev_hor_idle        -= sum(temp_df["idle"])
    rev_hor_utilized    -= sum(temp_df["utilized"])
    rev_hor_stalled     -= sum(temp_df["stalled"])
    temp_df = rev_start_df[(rev_start_df["output_dir"] == "W") & (rev_start_df["x"] == 8)]
    rev_hor_idle        -= sum(temp_df["idle"])
    rev_hor_utilized    -= sum(temp_df["utilized"])
    rev_hor_stalled     -= sum(temp_df["stalled"])
    for rf in range(self.rf_x):
      temp_df = rev_start_df[(rev_start_df["output_dir"] == "RE") & (rev_start_df["x"] == 7-rf)]
      rev_hor_idle        -= sum(temp_df["idle"])
      rev_hor_utilized    -= sum(temp_df["utilized"])
      rev_hor_stalled     -= sum(temp_df["stalled"])
      temp_df = rev_start_df[(rev_start_df["output_dir"] == "RW") & (rev_start_df["x"] == 8+rf)]
      rev_hor_idle        -= sum(temp_df["idle"])
      rev_hor_utilized    -= sum(temp_df["utilized"])
      rev_hor_stalled     -= sum(temp_df["stalled"])
         
    rev_hor_idle        /= (2*(1+self.rf_x)*NUM_TILES_Y*total_cycle)
    rev_hor_utilized    /= (2*(1+self.rf_x)*NUM_TILES_Y*total_cycle)
    rev_hor_stalled     /= (2*(1+self.rf_x)*NUM_TILES_Y*total_cycle)

    self.rev_hor_idle.append(rev_hor_idle)
    self.rev_hor_utilized.append(rev_hor_utilized)
    self.rev_hor_stalled.append(rev_hor_stalled)
    return


  # add csv row;
  def add_csv_row(self, df, network, direction, stat, cols):
    row = [network, direction, stat] + cols
    df.loc[len(df)] = row
    return

  # dump csv
  def dump_csv(self):
    # fwd df
    self.add_csv_row(self.fwd_output_df, "fwd", "ver", "idle", self.fwd_ver_idle)
    self.add_csv_row(self.fwd_output_df, "fwd", "ver", "utilized", self.fwd_ver_utilized)
    self.add_csv_row(self.fwd_output_df, "fwd", "ver", "stalled", self.fwd_ver_stalled)
    self.add_csv_row(self.fwd_output_df, "fwd", "hor", "idle", self.fwd_hor_idle)
    self.add_csv_row(self.fwd_output_df, "fwd", "hor", "utilized", self.fwd_hor_utilized)
    self.add_csv_row(self.fwd_output_df, "fwd", "hor", "stalled", self.fwd_hor_stalled)
    self.fwd_output_df.to_csv("fwd_bisection_bw.csv", sep=",")
    # rev df
    self.add_csv_row(self.rev_output_df, "rev", "ver", "idle", self.rev_ver_idle)
    self.add_csv_row(self.rev_output_df, "rev", "ver", "utilized", self.rev_ver_utilized)
    self.add_csv_row(self.rev_output_df, "rev", "ver", "stalled", self.rev_ver_stalled)
    self.add_csv_row(self.rev_output_df, "rev", "hor", "idle", self.rev_hor_idle)
    self.add_csv_row(self.rev_output_df, "rev", "hor", "utilized", self.rev_hor_utilized)
    self.add_csv_row(self.rev_output_df, "rev", "hor", "stalled", self.rev_hor_stalled)
    self.rev_output_df.to_csv("rev_bisection_bw.csv", sep=",")
    return


  # visualize
  def visualize(self):
    return



  



# main function;
if __name__ == "__main__":
  # arguments;
  hbench_path = sys.argv[1]
  rf_x = int(sys.argv[2])

  bw = BisectionBW(hbench_path, rf_x)
  bw.parse()
  bw.dump_csv()
  bw.visualize()
