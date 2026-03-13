import sys
import pandas as pd
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
  "gups_vcache"  : "apps/gups_rmw/tile-x_16__tile-y_8__A-size_1024__warm-cache_yes",
  "gups_dram"    : "apps/gups_rmw/tile-x_16__tile-y_8__A-size_67108864__warm-cache_no",
}

int_instr_execs = []
fp_instr_execs = []
local_load_execs = []
local_store_execs = []
remote_seq_ld_execs = []
remote_store_dram_execs = []
branch_execs = []
dram_stalls = []
dram_seq_stalls = []
amo_stalls = []
network_stalls = []
group_load_stalls =[]
wb_stalls = []
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

  # local load
  local_load_exec = stat["instr_local_ld"] / stat["total_cycle"]
  local_load_exec += stat["instr_local_flw"] / stat["total_cycle"]
  local_load_execs.append(local_load_exec)

  # local store
  local_store_exec = stat["instr_local_st"] / stat["total_cycle"]
  local_store_exec += stat["instr_local_fsw"] / stat["total_cycle"]
  local_store_execs.append(local_store_exec)

  # remote load seq dram;
  remote_seq_ld_exec = stat["instr_remote_seq_ld_dram"] / stat["total_cycle"]
  remote_seq_ld_exec += stat["instr_remote_seq_flw_dram"] / stat["total_cycle"]
  remote_seq_ld_execs.append(remote_seq_ld_exec)

  # remote store dram
  remote_store_dram_exec = stat["instr_remote_st_dram"] / stat["total_cycle"]
  remote_store_dram_exec += stat["instr_remote_fsw_dram"] / stat["total_cycle"]
  remote_store_dram_execs.append(remote_store_dram_exec)

  # branch exec
  branch_exec = stat["instr_beq"] / stat["total_cycle"]
  branch_exec += stat["instr_bne"] / stat["total_cycle"]
  branch_exec += stat["instr_blt"] / stat["total_cycle"]
  branch_exec += stat["instr_bge"] / stat["total_cycle"]
  branch_exec += stat["instr_bltu"] / stat["total_cycle"]
  branch_exec += stat["instr_bgeu"] / stat["total_cycle"]
  branch_exec += stat["instr_jal"] / stat["total_cycle"]
  branch_exec += stat["instr_jalr"] / stat["total_cycle"]
  branch_execs.append(branch_exec)

  # instr executed
  int_instr_exec = stat["non_fp_instr_exec"] / stat["total_cycle"]
  int_instr_exec -= local_load_exec
  int_instr_exec -= local_store_exec
  int_instr_exec -= branch_exec
  int_instr_exec -= remote_seq_ld_exec
  int_instr_exec -= remote_store_dram_exec
  int_instr_execs.append(int_instr_exec)

  # fp instr exec;
  fp_instr_execs.append(stat["fp_instr_exec"] / stat["total_cycle"])

  # dram stalls
  dram_stall = stat["stall_depend_dram_load"] / stat["total_cycle"]
  dram_stalls.append(dram_stall)

  # dram seq stall
  dram_seq_stall = stat["stall_depend_dram_seq_load"] / stat["total_cycle"]
  dram_seq_stalls.append(dram_seq_stall)

  # amo stall
  amo_stall = stat["stall_depend_dram_amo"] / stat["total_cycle"]
  amo_stall += stat["stall_amo_aq"] / stat["total_cycle"]
  amo_stall += stat["stall_amo_rl"] / stat["total_cycle"]
  amo_stalls.append(amo_stall)

  # network stalls
  network_stall = stat["stall_remote_req"] / stat["total_cycle"]
  network_stall += stat["stall_remote_credit"] / stat["total_cycle"]
  network_stalls.append(network_stall)
  
  # group load stall
  group_load_stall = stat["stall_depend_group_load"] / stat["total_cycle"]
  group_load_stalls.append(group_load_stall)

  # wb stall
  wb_stall  = stat["stall_remote_ld_wb"] / stat["total_cycle"]
  wb_stall += stat["stall_remote_flw_wb"] / stat["total_cycle"]
  wb_stalls.append(wb_stall)

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
  div_stall += stat["stall_depend_idiv"] / stat["total_cycle"]
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



# Data Frame for csv dump;
df_cols = ["stall_types"] + list(benchmark_paths.keys())
df = pd.DataFrame(columns=df_cols)

def add_layer(height, label, df):
  # df for csv;
  row = [label] + height
  df.loc[len(df)] = row

add_layer(int_instr_execs, "Int instr",  df)
add_layer(local_load_execs, "Local load",  df)
add_layer(local_store_execs, "Local store",  df)
add_layer(remote_seq_ld_execs, "Remote Seq Load",  df)
add_layer(remote_store_dram_execs, "Remote Store DRAM",  df)
add_layer(branch_execs, "Branch Jump",  df)
add_layer(fp_instr_execs, "FP instr",  df)
add_layer(dram_stalls, "Memory Sys stall",  df)
add_layer(dram_seq_stalls, "Memory Sys Seq stall",  df)
add_layer(amo_stalls, "AMO stall",  df)
add_layer(network_stalls, "Network stall",  df)
add_layer(group_load_stalls, "Group Load stall",  df)
add_layer(wb_stalls, "WB stall",  df)
add_layer(bypass_stalls, "Bypass stall",  df)
add_layer(branch_misses, "Branch miss",  df)
add_layer(div_stalls, "Div stall",  df)
add_layer(icache_misses, "icache miss",  df)
add_layer(fence_stalls, "Fence stall",  df)
add_layer(barrier_stalls, "Barrier stall",  df)


# export csv;
df.to_csv("core_stall_graph.csv", sep=",")
