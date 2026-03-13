import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from vcache_utilization import *
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
}
num_bench = len(benchmark_paths.keys())

vc_load = []
vc_store = []
vc_miss = []
vc_stall_rsp = []
vc_idle = []
dram_read = []
dram_write = []
dram_busy = []
dram_idle = []

for key in benchmark_paths.keys():
  # parse vcache stat
  vc_csv_path = hammerbench_path + "/" + benchmark_paths[key] + "/vcache_stats.csv"
  vc_stat = parse_vcache_stat(vc_csv_path)

  vc_load.append((vc_stat["load"] + vc_stat["atomic"]) / vc_stat["total"])
  vc_store.append(vc_stat["store"] / vc_stat["total"])
  vc_miss.append(vc_stat["miss"] / vc_stat["total"])
  vc_stall_rsp.append(vc_stat["stall_rsp"] / vc_stat["total"])
  vc_idle.append(vc_stat["idle"] / vc_stat["total"])

  # parse DRAM stat
  dram_csv_path = hammerbench_path + "/" + benchmark_paths[key] + "/blood_graph_stat.log"
  dram_stat = parse_dram_stat(dram_csv_path)

  dram_read.append(dram_stat["read"]/dram_stat["total"])
  dram_write.append(dram_stat["write"]/dram_stat["total"])
  dram_busy.append(dram_stat["busy"]/dram_stat["total"])
  dram_idle.append(dram_stat["idle"]/dram_stat["total"])



# Figure 0: vcache stalls;
fig0, ax0 = plt.subplots()
PLT_SCALE  = 4.0
PLT_WIDTH  = 5
PLT_HEIGHT = 4
fig0.set_size_inches(PLT_SCALE*PLT_WIDTH,PLT_SCALE*PLT_HEIGHT)


vc_bottoms = [0]*num_bench
xs = list(range(num_bench))

def add_layer_vc(height, label, color):
  ax0.bar(x=xs, height=height, bottom=vc_bottoms, label=label, width=0.4, color=color)
  for i in range(num_bench):
    vc_bottoms[i] += height[i]
  return

add_layer_vc(vc_load, "Load", "green")
add_layer_vc(vc_store, "Store", "lightgreen")
add_layer_vc(vc_miss, "Miss", "orange")
add_layer_vc(vc_stall_rsp, "Resp Stall", "purple")
add_layer_vc(vc_idle, "Idle", "lightgray")

# title
ax0.set_title("Vcache Utilization", fontsize=24)
# y-axis
ax0.set_ylabel("Vcache Cycle Composition", fontsize=20)
# x-axis
ax0.set_xticks(xs)
ax0.set_xticklabels(benchmark_paths.keys(), fontsize=20)
# legend
ax0.legend(fontsize=20,ncol=5, loc="upper center")

fig0.tight_layout()
fig0.savefig("vcache_stall.pdf", bbox_inches="tight")





# Figure 1: DRAM stall
fig1, ax1 = plt.subplots()
fig1.set_size_inches(PLT_SCALE*PLT_WIDTH,PLT_SCALE*PLT_HEIGHT)

dram_bottoms = [0]*num_bench
xs = list(range(num_bench))

def add_layer_dram(height, label, color):
  ax1.bar(x=xs, height=height, bottom=dram_bottoms, label=label, width=0.4, color=color)
  for i in range(num_bench):
    dram_bottoms[i] += height[i]
  return

add_layer_dram(dram_read, "Read",  "green")
add_layer_dram(dram_write, "Write", "lightgreen")
add_layer_dram(dram_busy, "Busy", "orange")
add_layer_dram(dram_idle, "Idle", "lightgray")

# title
ax1.set_title("HBM2 Utilization", fontsize=24)
# y axis
ax1.set_ylabel("DRAM Cycle Composition", fontsize=20)
# x axis
ax1.set_xticks(xs)
ax1.set_xticklabels(benchmark_paths.keys(), fontsize=20)
# legend
ax1.legend(fontsize=20,ncol=4, loc="upper center")

fig1.tight_layout()
fig1.savefig("dram_stall.pdf", bbox_inches="tight")
# show
#plt.show()
