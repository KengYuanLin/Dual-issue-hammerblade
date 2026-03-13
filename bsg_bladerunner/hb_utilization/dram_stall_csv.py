import sys
import pandas as pd
from dram_utilization import *

# arguments
hammerbench_path = sys.argv[1]

benchmark_paths = {
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

busys = []
reads = []
writes = []
idles = []

for key in benchmark_paths.keys():
  # parse stat
  csv_path = hammerbench_path + "/" + benchmark_paths[key] + "/blood_graph_stat.log"
  stat = parse_dram_stat(csv_path)

  busys.append(stat["busy"]/stat["total"])
  reads.append(stat["read"]/stat["total"])
  writes.append(stat["write"]/stat["total"])
  idles.append(stat["idle"]/stat["total"])
  

# empty data frame;
df_cols = ["Label"] + list(benchmark_paths.keys())
df = pd.DataFrame(columns=df_cols)

def add_row(label, cols):
  row = [label] + cols
  df.loc[len(df)] = row

add_row("busy", busys)
add_row("read", reads)
add_row("write", writes)
add_row("idle", idles)

# export csv;
df.to_csv("dram_stall_graph.csv", sep=",")
