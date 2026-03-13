import pandas as pd

FP_INSTR_TYPES = [
  "instr_fadd",
  "instr_fsub",

  "instr_fmul",
  "instr_fmadd",
  "instr_fmsub",
  "instr_fnmadd",
  "instr_fnmsub",

  "instr_fdiv",
  "instr_fsqrt",
]

MEM_INSTR_TYPES = [
    "instr_local_ld",
    "instr_local_st",
    "instr_remote_ld_dram",
    "instr_remote_seq_ld_dram",
    "instr_remote_ld_global",
    "instr_remote_ld_group",
    "instr_remote_st_dram",
    "instr_remote_st_global",
    "instr_remote_st_group",
    "instr_local_flw",
    "instr_local_fsw",
    "instr_remote_flw_dram",
    "instr_remote_seq_flw_dram",
    "instr_remote_flw_global",
    "instr_remote_flw_group",
    "instr_remote_fsw_dram",
    "instr_remote_fsw_global",
    "instr_remote_fsw_group",
]

def parse_vanilla_stat(filename="vanilla_stats.csv"):
  try:
    df = pd.read_csv(filename)
  except:
    print("{} not found.".format(filename))
    return None

  tags = df["tag"]
  timestamps = df["global_ctr"]
  
  bubble_cols = list(filter(lambda x: x.startswith("bubble_"), list(df)))
  stall_cols = list(filter(lambda x: x.startswith("stall_"), list(df)))
  instr_cols = list(filter(lambda x: x.startswith("instr_"), list(df)))
  instr_cols.remove("instr_total")
  #print(bubble_cols)
  #print(stall_cols)
  total_cycle = 0
  instr_cycle = 0
  total_bubble_cycle = 0
  total_stall_cycle = 0
  fp_instr_executed = 0
  mem_instr_executed = 0

  # for each bubble and stall type
  each_bubble_cycle = {}
  each_stall_cycle = {}
  each_instr_cycle = {}
  for col in bubble_cols:
    each_bubble_cycle[col] = 0
  for col in stall_cols:
    each_stall_cycle[col] = 0
  for col in instr_cols:
    each_instr_cycle[col] = 0

  
  # calculate cycle
  start_count = 0
  end_count = 0
  start_timestamp = (2**32)-1
  end_timestamp = 0
  for i in range(len(tags)):
    tag = tags[i]
    timestamp = timestamps[i]
    tag_type = (0xc0000000 & tag) >> 30

    instr_total = df["instr_total"][i]
    fp_instr_total = 0
    for fpt in FP_INSTR_TYPES:
      fp_instr_total += df[fpt][i]
    mem_instr_total = 0
    for fpt in MEM_INSTR_TYPES:
      mem_instr_total += df[fpt][i]

    # kernel start
    if tag_type == 2:
      start_count += 1
      if timestamp < start_timestamp:
        start_timestamp = timestamp
      total_cycle -= timestamp
      instr_cycle -= instr_total
      fp_instr_executed -= fp_instr_total
      mem_instr_executed -= mem_instr_total
      for col in bubble_cols:
        total_bubble_cycle     -= df[col][i]
        each_bubble_cycle[col] -= df[col][i]
      for col in stall_cols:
        total_stall_cycle      -= df[col][i]
        each_stall_cycle[col]  -= df[col][i]
      for col in instr_cols:
        each_instr_cycle[col] -= df[col][i]
      
    # kernel end
    elif tag_type == 3:
      end_count += 1
      if timestamp > end_timestamp:
        end_timestamp = timestamp
      total_cycle += timestamp
      instr_cycle += instr_total
      fp_instr_executed += fp_instr_total
      mem_instr_executed += mem_instr_total
      for col in bubble_cols:
        total_bubble_cycle += df[col][i]
        each_bubble_cycle[col] += df[col][i]
      for col in stall_cols:
        total_stall_cycle  += df[col][i]
        each_stall_cycle[col]  += df[col][i]
      for col in instr_cols:
        each_instr_cycle[col] += df[col][i]

  if (start_count == 0) or (start_count != end_count):
    print("Error: vanilla_stat start and end count do not match or exist.", start_count, end_count)
    return None

  # build stat dict
  curr_stat = {}
  curr_stat["runtime"] = end_timestamp - start_timestamp
  curr_stat["util_pct"] = instr_cycle/total_cycle*100
  curr_stat["total_cycle"] = total_cycle
  curr_stat["total_stall_cycle"] = total_stall_cycle
  curr_stat["total_bubble_cycle"] = total_bubble_cycle
  for col in stall_cols:
    curr_stat[col] = each_stall_cycle[col]
  for col in bubble_cols:
    curr_stat[col] = each_bubble_cycle[col]
  for col in instr_cols:
    curr_stat[col] = each_instr_cycle[col]

  curr_stat["non_fp_instr_exec"] = instr_cycle-fp_instr_executed
  curr_stat["fp_instr_exec"] = fp_instr_executed
  curr_stat["mem_instr_exec"] = mem_instr_executed
  curr_stat["total_instr_exec"] = instr_cycle
  
  return curr_stat
  

def print_vanilla_stat(stat):
  print("")
  print("--------------------------------")
  print("Core Utilization")

  print("--------------------------------")
  keys = list(stat.keys())
  stall_cols = list(filter(lambda x: x.startswith("stall"), keys))
  for col in stall_cols:
    if stat[col] != 0:
      print("{:<{w1}} = {:<{w2}} ({:.2f} %)".format(col, stat[col], stat[col]/stat["total_cycle"]*100, w1=30, w2=12))
  print("{:<{w1}} = {:<{w2}} ({:.2f} %)".format("Total Stall", stat["total_stall_cycle"], stat["total_stall_cycle"]/stat["total_cycle"]*100, w1=30, w2=12))

  print("--------------------------------")
  bubble_cols = list(filter(lambda x: x.startswith("bubble"), keys))
  for col in bubble_cols:
    if stat[col] != 0:
      print("{:<{w1}} = {:<{w2}} ({:.2f} %)".format(col, stat[col], stat[col]/stat["total_cycle"]*100, w1=30, w2=12))
  print("{:<{w1}} = {:<{w2}} ({:.2f} %)".format("Total Bubble", stat["total_bubble_cycle"], stat["total_bubble_cycle"]/stat["total_cycle"]*100, w1=30, w2=12))

  print("--------------------------------")
  instr_cols = list(filter(lambda x: x.startswith("instr"), keys))
  for col in instr_cols:
    if stat[col] != 0:
      print("{:<{w1}} = {:<{w2}} ({:.2f} %)".format(col.replace("instr_", ""), stat[col], stat[col]/stat["total_instr_exec"]*100, w1=30, w2=12))
      
  #print("Non-FP  Instr Executed   = {:<{w}}".format(stat["non_fp_instr_exec"], w=12))
  #print("FP      Instr Executed   = {:<{w}}".format(stat["fp_instr_exec"], w=12))
  print("Total Instr Executed   = {:<{w}}".format(stat["total_instr_exec"], w=12))
  print("--------------------------------")
  print("Utilization   = {:.2f} %".format(stat["util_pct"]))
  print("--------------------------------")
  print("Runtime       = {} cycles".format(stat["runtime"]))
  print("--------------------------------")



def summarize_core_stall(stat):
  # Instr exec;
  int_instr_exec = stat["non_fp_instr_exec"] - stat["mem_instr_exec"]
  fp_instr_exec = stat["fp_instr_exec"]
  mem_instr_exec = stat["mem_instr_exec"]
  # mem exec;
  
  # DRAM stall;
  dram_stall = stat["stall_depend_dram_load"]
  dram_stall += stat["stall_depend_dram_seq_load"]
  dram_stall += stat["stall_depend_dram_amo"]
  dram_stall += stat["stall_amo_aq"]
  dram_stall += stat["stall_amo_rl"]
  # network stall;
  network_stall = stat["stall_remote_req"]
  network_stall += stat["stall_remote_ld_wb"]
  network_stall += stat["stall_remote_flw_wb"]
  network_stall += stat["stall_remote_credit"]
  network_stall += stat["stall_depend_group_load"]
  # bypass
  bypass_stall = stat["stall_depend_local_load"]
  bypass_stall += stat["stall_depend_imul"]
  bypass_stall += stat["stall_bypass"]
  # branch miss
  branch_miss = stat["bubble_branch_miss"]
  branch_miss += stat["bubble_jalr_miss"]
  # div stall
  div_stall = stat["stall_depend_fdiv"]
  div_stall += stat["stall_depend_idiv"]
  div_stall += stat["stall_fdiv_busy"]
  div_stall += stat["stall_idiv_busy"]
  # barrier stall
  barrier_stall = stat["stall_barrier"]
  barrier_stall += stat["stall_lr_aq"]
  # other stall
  other_stall = stat["stall_ifetch_wait"]
  other_stall += stat["bubble_icache_miss"]
  #other_stall += stat["miss_icache"]
  other_stall += stat["stall_fence"]

  print("Stall Summary")
  print("IntInstrExec    = {:.2f} %".format(100*int_instr_exec/stat["total_cycle"]))
  print("FPInstrExec     = {:.2f} %".format(100*fp_instr_exec/stat["total_cycle"]))
  print("MEMInstrExec    = {:.2f} %".format(100*mem_instr_exec/stat["total_cycle"]))
  print("MemorySysStall  = {:.2f} %".format(100*dram_stall/stat["total_cycle"]))
  print("NetworkStall    = {:.2f} %".format(100*network_stall/stat["total_cycle"]))
  print("BypassStall     = {:.2f} %".format(100*bypass_stall/stat["total_cycle"]))
  print("BranceMiss      = {:.2f} %".format(100*branch_miss/stat["total_cycle"]))
  print("DivStall        = {:.2f} %".format(100*div_stall/stat["total_cycle"]))
  print("BarrierStall    = {:.2f} %".format(100*barrier_stall/stat["total_cycle"]))
  print("OtherStall      = {:.2f} %".format(100*other_stall/stat["total_cycle"]))
  

