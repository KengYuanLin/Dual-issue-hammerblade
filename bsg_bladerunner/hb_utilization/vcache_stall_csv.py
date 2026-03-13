import sys
import pandas as pd
from vcache_utilization import *

# arguments
hammerbench_path = sys.argv[1]

# benchmark paths;
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

# buckets;
loads       = []
stores      = []
atomics     = []
misses      = []
stall_rsps  = []
idles       = []


for key in benchmark_paths.keys():
  # parse vcache stats;
  csv_path = hammerbench_path + "/" + benchmark_paths[key] + "/vcache_stats.csv"
  stat = parse_vcache_stat(csv_path)
  # put metrics in the buckets;
  loads.append(stat["load"]/stat["total"])
  stores.append(stat["store"]/stat["total"])
  atomics.append(stat["atomic"]/stat["total"])
  misses.append(stat["miss"]/stat["total"])
  stall_rsps.append(stat["stall_rsp"]/stat["total"])
  idles.append(stat["idle"]/stat["total"])

# empty data frame;
df_cols = ["Label"] + list(benchmark_paths.keys())
df = pd.DataFrame(columns=df_cols)

# add rows;
def add_row(label, cols):
  row = [label] + cols
  df.loc[len(df)] = row

add_row("load", loads)
add_row("store", stores)
add_row("atomic", atomics)
add_row("miss", misses)
add_row("stall_rsp", stall_rsps)
add_row("idle", idles)

# export csv;
df.to_csv("vcache_stall_graph.csv", sep=",")
