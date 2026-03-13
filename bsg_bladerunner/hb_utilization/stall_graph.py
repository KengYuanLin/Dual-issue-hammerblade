import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from core_utilization import *

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

# plt fig
fig, ax = plt.subplots()
PLT_SCALE  = 4.0
PLT_WIDTH  = 6
PLT_HEIGHT = 4
fig.set_size_inches(PLT_SCALE*PLT_WIDTH,PLT_SCALE*PLT_HEIGHT)


# collect stats
int_instr_execs = []
fp_instr_execs = []
dram_stalls = []
network_stalls = []
bypass_stalls = []
branch_misses = []
icache_misses = []
div_stalls = []
fence_stalls = []
barrier_stalls = []

for key in benchmark_paths.keys():
  # parse stat
  csv_path = hammerbench_path + "/" + benchmark_paths[key] + "/vanilla_stats.csv"
  stat = parse_vanilla_stat(csv_path)
  # instr executed
  int_instr_execs.append(stat["non_fp_instr_exec"] / stat["total_cycle"])
  fp_instr_execs.append(stat["fp_instr_exec"] / stat["total_cycle"])
  # dram stalls
  dram_stall = stat["stall_depend_dram_load"] / stat["total_cycle"]
  dram_stall += stat["stall_depend_dram_seq_load"] / stat["total_cycle"]
  dram_stall += stat["stall_depend_dram_amo"] / stat["total_cycle"]
  dram_stall += stat["stall_amo_aq"] / stat["total_cycle"]
  dram_stalls.append(dram_stall)
  # network stalls
  network_stall = stat["stall_remote_req"] / stat["total_cycle"]
  network_stall += stat["stall_remote_ld_wb"] / stat["total_cycle"]
  network_stall += stat["stall_remote_flw_wb"] / stat["total_cycle"]
  network_stall += stat["stall_remote_credit"] / stat["total_cycle"]
  network_stall += stat["stall_depend_group_load"] / stat["total_cycle"]
  network_stalls.append(network_stall)
  # bypass
  bypass_stall = stat["stall_depend_local_load"] / stat["total_cycle"]
  bypass_stall += stat["stall_depend_imul"] / stat["total_cycle"]
  bypass_stall += stat["stall_bypass"] / stat["total_cycle"]
  bypass_stalls.append(bypass_stall)
  # branch miss
  branch_miss  = stat["bubble_branch_miss"] / stat["total_cycle"]
  branch_miss += stat["bubble_jalr_miss"] / stat["total_cycle"]
  branch_misses.append(branch_miss)
  # div stall
  div_stall = stat["stall_depend_fdiv"] / stat["total_cycle"]
  div_stall += stat["stall_fdiv_busy"] / stat["total_cycle"]
  div_stall += stat["stall_idiv_busy"] / stat["total_cycle"]
  div_stalls.append(div_stall)
  # icache miss
  icache_miss = stat["stall_ifetch_wait"] / stat["total_cycle"]
  icache_miss += stat["bubble_icache_miss"] / stat["total_cycle"]
  icache_misses.append(icache_miss)
  # fence stall
  fence_stall = stat["stall_fence"] / stat["total_cycle"]
  fence_stalls.append(fence_stall)
  # barrier stall
  barrier_stall = stat["stall_barrier"] / stat["total_cycle"]
  barrier_stalls.append(barrier_stall)



# make bar graph
num_bench = len(benchmark_paths.keys())
bottoms = [0]*num_bench
xs = list(range(num_bench))

# add empty bar
plt.bar(x=num_bench,height=0,width=2)


# Data Frame for csv dump;
df_cols = ["stall_types"] + list(benchmark_paths.keys())
df = pd.DataFrame(columns=df_cols)

def add_layer(height, label, color, df):
  # df for csv;
  row = [label] + height
  df.loc[len(df)] = row
  # bar graph
  plt.bar(x=xs, height=height, bottom=bottoms, label=label, width=0.4, color=color)
  for i in range(num_bench):
    bottoms[i] += height[i]
  return

add_layer(int_instr_execs, "Int instr", "green", df)
add_layer(fp_instr_execs, "FP instr", "lightgreen", df)
add_layer(dram_stalls, "Memory Sys stall", "gold", df)
add_layer(network_stalls, "Network stall", "orange", df)
add_layer(bypass_stalls, "Bypass stall", "purple", df)
add_layer(branch_misses, "Branch miss", "magenta", df)
add_layer(div_stalls, "Div stall", "brown", df)
add_layer(icache_misses, "icache miss", "navy", df)
add_layer(fence_stalls, "Fence stall", "gray", df)
add_layer(barrier_stalls, "Barrier stall", "darkgray", df)


# export csv;
df.to_csv("stall_graph.csv", sep=",")

# y axis
plt.ylabel("Cycle composition", fontsize=22)

# x axis
plt.xticks(xs, benchmark_paths.keys(), fontsize=20)

# legend
plt.legend(loc="upper right", fontsize=22)
# show
fig.tight_layout()
plt.savefig("stall_graph.pdf", bbox_inches="tight")
plt.show()
