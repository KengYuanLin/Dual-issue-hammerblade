#
#   periodic_stat.py 
#
#   How to use:
#   python periodic_stat.py {path_to_test_dir}
#
#   Make sure that you have the following files in the test dir;
#   - router_periodic_stat.csv 
#   - blood_graph_periodic_stat.csv 
#   - vcache_periodic_stat.csv 
#   - vanilla_periodic_stat.csv
#   - blood_graph_stat.log
#   - vcache_stats.csv
#
#   This will produce "periodic_stat.pdf"
#

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

# Plot dimension;
PLT_SCALE = 0.5
PLT_WIDTH  = 28 * PLT_SCALE
#PLT_HEIGHT = 4.5 * NUM_PLOTS_Y * PLT_SCALE


# constants;
DRAM_PERIOD   = 250
VCACHE_PERIOD = 250
ROUTER_PERIOD = 250
CORE_PERIOD   = 250
NUM_VCACHE    = 32
POD_ORIGIN_X  = 16
POD_ORIGIN_Y  = 8
NUM_TILES_X   = 16
NUM_TILES_Y   = 8
RF_X          = 3



class PeriodicStatVisualizer:
  # constructor;
  def __init__(self, bpath):
    self.bpath = bpath
    self.find_end_timestamp()

  # visualize
  def visualize(self, plots):
    fig, axs = plt.subplots(len(plots),1)
    fig.set_size_inches(PLT_WIDTH,len(plots)*PLT_SCALE*4.5)

    # load router data
    df = self.open_csv(self.bpath + "/router_periodic_stat.csv")
    df["x"] = df["x"].subtract(POD_ORIGIN_X)
    df["y"] = df["y"].subtract(POD_ORIGIN_Y)
    df["output_dir"] = df.apply(lambda x: self.convert_dir(x.output_dir), axis=1)
    df = df[(df["x"] >= 0) & (df["x"] < NUM_TILES_X)]
    self.network_df = df[(df["y"] >= 0) & (df["y"] < NUM_TILES_Y)]

    curr_ax = 0
    # figure : core util
    if "Core" in plots:
      self.plot_core(fig, axs[curr_ax])
      curr_ax += 1

    # figure : vcache
    if "Cache" in plots:
      self.plot_vcache(fig, axs[curr_ax])
      curr_ax += 1

    # figure : DRAM
    if "DRAM" in plots:
      self.plot_dram(fig, axs[curr_ax])
      curr_ax += 1

    # figure : network
    if "noc-tile-cache" in plots:
      self.plot_network_tile_vcache(fig, axs[curr_ax])
      curr_ax += 1
    if "noc-fwd-horiz" in plots:
      self.plot_network_fwd_hor(fig, axs[curr_ax])
      curr_ax += 1
    if "noc-fwd-vert" in plots:
      self.plot_network_fwd_ver(fig, axs[curr_ax])
      curr_ax += 1
    if "noc-rev-horiz" in plots:
      self.plot_network_rev_hor(fig, axs[curr_ax])
      curr_ax += 1
    if "noc-rev-vert" in plots:
      self.plot_network_rev_ver(fig, axs[curr_ax])
      curr_ax += 1


    # finish up;
    fig.tight_layout(pad=0.5)
    plt.savefig("periodic_stat.pdf", bbox_inches="tight")
    plt.savefig("periodic_stat.png", bbox_inches="tight")
    plt.close()
    return

  # Plot DRAM
  def plot_dram(self, fig, ax):
    # parse period stat csv;
    period_df = self.open_csv(self.bpath + "/blood_graph_periodic_stat.csv")

    # xs
    xs = []
    # ys
    ys_ref = []
    ys_read = []
    ys_write = []
    ys_busy = []
    ys_idle = []
    # make array;
    for i in range(len(period_df)-1):
      x0 = period_df["timestamp"].iloc[i]
      x1 = period_df["timestamp"].iloc[i+1]
      busy0 = period_df["busy"].iloc[i]
      busy1 = period_df["busy"].iloc[i+1]
      ref0 = period_df["refresh"].iloc[i]
      ref1 = period_df["refresh"].iloc[i+1]
      read0 = period_df["read"].iloc[i]
      read1 = period_df["read"].iloc[i+1]
      write0 = period_df["write"].iloc[i]
      write1 = period_df["write"].iloc[i+1]
      if x1 < self.dram_end_timestamp:
        xs.append((x1+x0)/2)
        y_ref = (ref1 - ref0) / DRAM_PERIOD * 100
        y_read = (read1 - read0) / DRAM_PERIOD * 100
        y_write = (write1 - write0) / DRAM_PERIOD * 100
        y_busy = (busy1 - busy0) / DRAM_PERIOD * 100
        y_idle = 100.0 - y_ref - y_read - y_write - y_busy
        ys_ref.append(y_ref)
        ys_read.append(y_read)
        ys_write.append(y_write)
        ys_busy.append(y_busy)
        ys_idle.append(y_idle)

    # stackplot
    labels = ["refresh", "read", "write", "busy", "idle"]
    colors = ["black", "green", "lightgreen", "orange", "gray"]
    ax.stackplot(xs, ys_ref, ys_read, ys_write, ys_busy, ys_idle, labels=labels, colors=colors, step="post")
    ax.set_xticks([])
    #ax.set_xticklabels([int(xs[-1]-xs[0])])
    ax.legend(ncol=6, loc="lower center", bbox_to_anchor=(0.5,-0.23))
    ax.set_title("DRAM utilization")
    #ax.set_xlim(xs[0], xs[0]+120250)
    ax.set_xlim(xs[0], xs[-1])
    ax.set_ylim(0,100)
    ax.set_yticks([])
    return

  # Plot vcache
  def plot_vcache(self, fig, ax):
    # parse periodic stat;
    period_df = self.open_csv(self.bpath + "/vcache_periodic_stats.csv")
      
    # groupby
    group_df = period_df.groupby("global_ctr")
    ts = list(group_df.groups.keys())
    ts.sort()
    # xs
    xs = []
    # ys
    groupby_load = group_df["load"].sum()
    groupby_store = group_df["store"].sum()
    groupby_atomic = group_df["atomic"].sum()
    groupby_miss = group_df["miss"].sum()
    groupby_stall_rsp = group_df["stall_rsp"].sum()
    groupby_idle = group_df["idle"].sum()
    ys_load = []
    ys_store = []
    ys_atomic = []
    ys_miss = []
    ys_stall_rsp = []
    ys_idle = []
    for i in range(len(ts)-1):
      t0 = ts[i]
      t1 = ts[i+1]
      if t1 < self.end_timestamp:
        xs.append((t1+t0)/2)
        y_load = (groupby_load[t1] - groupby_load[t0]) / (VCACHE_PERIOD * NUM_VCACHE) * 100
        y_store = (groupby_store[t1] - groupby_store[t0]) / (VCACHE_PERIOD * NUM_VCACHE) * 100
        y_atomic = (groupby_atomic[t1] - groupby_atomic[t0]) / (VCACHE_PERIOD * NUM_VCACHE) * 100
        y_miss = (groupby_miss[t1] - groupby_miss[t0]) / (VCACHE_PERIOD * NUM_VCACHE) * 100
        y_stall_rsp = (groupby_stall_rsp[t1] - groupby_stall_rsp[t0]) / (VCACHE_PERIOD * NUM_VCACHE) * 100
        y_idle = (groupby_idle[t1] - groupby_idle[t0]) / (VCACHE_PERIOD * NUM_VCACHE) * 100
        ys_load.append(y_load)
        ys_store.append(y_store)
        ys_atomic.append(y_atomic)
        ys_miss.append(y_miss)
        ys_stall_rsp.append(y_stall_rsp)
        ys_idle.append(y_idle)
    # stackplot
    labels = ["Load", "Store", "miss", "atomic", "resp stall", "Idle"]
    colors = ["green", "lightgreen", "orange", "brown", "purple", "gray"]

    ax.stackplot(xs, ys_load, ys_store, ys_miss, ys_atomic, ys_stall_rsp, ys_idle, labels=labels, colors=colors, step="post")
    ax.set_xticks([])
    #ax.set_xticklabels([int(xs[-1]-xs[0])])
    ax.set_title("Vcache utilization")
    ax.legend(ncol=6, loc="lower center", bbox_to_anchor=(0.5,-0.23))
    #ax.set_xlim(xs[0], xs[0]+180750)
    ax.set_xlim(xs[0], xs[-1])
    ax.set_ylim(0,100)
    return

  # Plot core util
  def plot_core(self, fig, ax):
    # read csv and group
    df = self.open_csv(self.bpath + "/vanilla_periodic_stats.csv")
    group_df = df.groupby("global_ctr")

    # Columns;
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
    bubble_cols = list(filter(lambda x: x.startswith("bubble_"), list(df)))
    stall_cols = list(filter(lambda x: x.startswith("stall_"), list(df)))
    stall_cols.append("miss_icache")

    # ts
    ts = list(group_df.groups.keys())
    ts.sort()

    # groupby sum
    group_instr_total = group_df["instr_total"].sum()
    group_instr_fp = {}
    group_stall = {}
    for col in FP_INSTR_TYPES:
      group_instr_fp[col] = group_df[col].sum()
    for col in bubble_cols:
      group_stall[col] = group_df[col].sum()
    for col in stall_cols:
      group_stall[col] = group_df[col].sum()
    
    # xs
    xs = []
    # ys
    ys_int_exec = []
    ys_fp_exec = []
    ys_dram_stall = []
    ys_network_stall = []
    ys_bypass_stall = []
    ys_branch_miss = []
    ys_icache_miss = []
    ys_div_stall = []
    ys_fence_stall = []
    ys_barrier_stall = []
    # DENOM
    DENOM = CORE_PERIOD * NUM_TILES_X * NUM_TILES_Y / 100
    for i in range(len(ts)-1):
      t0 = ts[i]
      t1 = ts[i+1]
      if t1 < self.end_timestamp:
        xs.append((t0+t1)/2)
        # fp exec
        y_fp_exec = 0
        for col in FP_INSTR_TYPES:
          y_fp_exec += (group_instr_fp[col][t1] - group_instr_fp[col][t0])
        ys_fp_exec.append(y_fp_exec / DENOM)
        # int exec
        y_int_exec = (group_instr_total[t1] - group_instr_total[t0])
        y_int_exec -= y_fp_exec
        ys_int_exec.append(y_int_exec / DENOM)

        # dram stall
        DRAM_STALL_COLS = [
          "stall_depend_dram_load",
          "stall_depend_dram_seq_load",
          "stall_depend_dram_amo",
          "stall_amo_aq",
          "stall_amo_rl",
        ]
        y_dram_stall = 0
        for col in DRAM_STALL_COLS:
          y_dram_stall += (group_stall[col][t1] - group_stall[col][t0])
        ys_dram_stall.append(y_dram_stall / DENOM)

        # network stall
        NETWORK_STALL_COLS = [
          "stall_remote_req",
          "stall_remote_ld_wb",
          "stall_remote_flw_wb",
          "stall_remote_credit",
          "stall_depend_group_load",
        ]
        y_network_stall = 0
        for col in NETWORK_STALL_COLS:
          y_network_stall += (group_stall[col][t1] - group_stall[col][t0])
        ys_network_stall.append(y_network_stall / DENOM)

        # bypass stall
        BYPASS_STALL_COLS = [
          "stall_depend_local_load",
          "stall_depend_imul",
          "stall_bypass",
        ]
        y_bypass_stall = 0
        for col in BYPASS_STALL_COLS:
          y_bypass_stall += (group_stall[col][t1] - group_stall[col][t0])
        ys_bypass_stall.append(y_bypass_stall / DENOM)

        # branch miss
        BRANCH_MISS_COLS = [
          "bubble_branch_miss",
          "bubble_jalr_miss"
        ]
        y_branch_miss = 0
        for col in BRANCH_MISS_COLS:
          y_branch_miss += (group_stall[col][t1] - group_stall[col][t0])
        ys_branch_miss.append(y_branch_miss / DENOM)

        # icache miss
        ICACHE_MISS_COLS = [
          "stall_ifetch_wait",
          "bubble_icache_miss",
          "miss_icache"
        ]
        y_icache_miss= 0
        for col in ICACHE_MISS_COLS:
          y_icache_miss += (group_stall[col][t1] - group_stall[col][t0])
        ys_icache_miss.append(y_icache_miss/ DENOM)

        # div stall
        DIV_STALL_COLS = [
          "stall_depend_fdiv",
          "stall_depend_idiv",
          "stall_fdiv_busy",
          "stall_idiv_busy",
        ]
        y_div_stall = 0
        for col in DIV_STALL_COLS:
          y_div_stall += (group_stall[col][t1] - group_stall[col][t0])
        ys_div_stall.append(y_div_stall/ DENOM)

        # fence stall
        FENCE_STALL_COLS = [
          "stall_fence"
        ]
        y_fence_stall = 0
        for col in FENCE_STALL_COLS:
          y_fence_stall += (group_stall[col][t1] - group_stall[col][t0])
        ys_fence_stall.append(y_fence_stall/ DENOM)

        # barrier stall
        BARRIER_STALL_COLS = [
          "stall_barrier",
          "stall_lr_aq"
        ]
        y_barrier_stall = 0
        for col in BARRIER_STALL_COLS:
          y_barrier_stall += (group_stall[col][t1] - group_stall[col][t0])
        ys_barrier_stall.append(y_barrier_stall/ DENOM)

    # stack plot
    labels = ["Int Instr", "FP Instr", "MemorySys stall", "Network stall", "Bypass stall",
            "Branch miss", "Div stall", "icache miss", "Fence stall", "Barrier stall"]
    colors = ["green", "lightgreen", "gold", "orange", "purple",
              "magenta", "brown", "navy", "gray", "darkgray"]
    ax.stackplot(xs,
      ys_int_exec, ys_fp_exec, ys_dram_stall, ys_network_stall, ys_bypass_stall,
      ys_branch_miss, ys_div_stall, ys_icache_miss, ys_fence_stall, ys_barrier_stall,
      labels=labels, colors=colors, step="post")
    ax.set_xticks([])
    #ax.set_xticklabels([int(xs[-1]-xs[0])])
    ax.set_title("Core utilization")
    ax.legend(ncol=5, loc="lower center", bbox_to_anchor=(0.5,-0.38))
    #ax.set_xlim(xs[0], xs[0]+180750)
    ax.set_xlim(xs[0], xs[-1])
    ax.set_ylim(0,100)
    return

  # network fwd hor;
  def plot_network_fwd_hor(self, fig, ax):
    def cond(df):
      cond =  (df["output_dir"] == "E") & (df["x"] == ((NUM_TILES_X/2)-1))
      cond |= (df["output_dir"] == "W") & (df["x"] == ((NUM_TILES_X/2)))
      for i in range(RF_X):
        cond |=  (df["output_dir"] == "RE") & (df["x"] == ((NUM_TILES_X/2)-1-i))
        cond |= (df["output_dir"] == "RW") & (df["x"] == ((NUM_TILES_X/2)+i))
      return df[cond]
    denom = 2*NUM_TILES_Y*(1+RF_X)*ROUTER_PERIOD / 100
    self.plot_router_util(fig, ax, 1, cond, "Network FWD Horizontal", denom)
    return


  # network fwd ver;
  def plot_network_fwd_ver(self, fig, ax):
    def cond(df):
      cond =  (df["output_dir"] == "S") & (df["y"] == ((NUM_TILES_Y/2)-1))
      cond |= (df["output_dir"] == "N") & (df["y"] == ((NUM_TILES_Y/2)))
      return df[cond]

    denom = 2 * NUM_TILES_X*ROUTER_PERIOD / 100
    self.plot_router_util(fig, ax, 1, cond, "Network FWD Vertical", denom)
    return

  # network rev hor;
  def plot_network_rev_hor(self, fig, ax):
    def cond(df):
      cond =  (df["output_dir"] == "E") & (df["x"] == ((NUM_TILES_X/2)-1))
      cond |= (df["output_dir"] == "W") & (df["x"] == ((NUM_TILES_X/2)))
      for i in range(RF_X):
        cond |=  (df["output_dir"] == "RE") & (df["x"] == ((NUM_TILES_X/2)-1-i))
        cond |= (df["output_dir"] == "RW") & (df["x"] == ((NUM_TILES_X/2)+i))
      return df[cond]
      
    denom = 2*NUM_TILES_Y * (1+RF_X)*ROUTER_PERIOD / 100
    self.plot_router_util(fig, ax, 0, cond, "Network Rev Horizontal", denom)
    return

  # network rev ver;
  def plot_network_rev_ver(self, fig, ax):
    def cond(df):
      cond =  (df["output_dir"] == "S") & (df["y"] == ((NUM_TILES_Y/2)-1))
      cond |= (df["output_dir"] == "N") & (df["y"] == ((NUM_TILES_Y/2)))
      return df[cond]

    denom = 2 * NUM_TILES_X*ROUTER_PERIOD / 100
    self.plot_router_util(fig, ax, 0, cond, "Network Rev Vertical", denom)
    return

  # network tile vcache;
  def plot_network_tile_vcache(self, fig, ax):
    def cond(df):
      cond =  (df["output_dir"] == "N") & (df["y"] == 0)
      cond |= (df["output_dir"] == "S") & (df["y"] == (NUM_TILES_Y-1))
      return df[cond]

    denom = 2*NUM_TILES_X*ROUTER_PERIOD / 100
    self.plot_router_util(fig, ax, 1, cond, "Network tile-vcache", denom)
    return

  #                     #
  #   HELPER ROUTINES   #
  #                     #

  # open csv
  def open_csv(self, csv_path):
    try:
      return pd.read_csv(csv_path)
    except:
      print("[Error] open_csv(): {} not found.".format(csv_path))
      sys.exit(1)
    
  # use the vcache stat to find the end timestamp;
  def find_end_timestamp(self):
    # DRAM
    df = self.open_csv(self.bpath + "/blood_graph_stat.log")
    # find the end timestamp;
    tags = df["tag"]
    timestamps = df["timestamp"]
    self.dram_end_timestamp = 0
    for i in range(len(tags)):
      tag = tags[i]
      timestamp = timestamps[i]
      tag_type = (0xc0000000 & tag) >> 30
      if tag_type == 3:
        if self.dram_end_timestamp < timestamp:
          self.dram_end_timestamp = timestamp


    df = self.open_csv(self.bpath + "/vcache_stats.csv")
    # find the end timestamp;
    timestamps = df["global_ctr"]
    tags = df["tag"]
    self.end_timestamp = 0
    for i in range(len(tags)):
      tag = tags[i]
      timestamp = timestamps[i]
      tag_type = (0xc0000000 & tag) >> 30
      if tag_type == 3:
        if self.end_timestamp < timestamp:
          self.end_timestamp = timestamp
    return

  # convert dir;
  def convert_dir(self, d):
    dir_map = {
      0 : "P",
      1 : "W",
      2 : "E",
      3 : "N",
      4 : "S",
      5 : "RW",
      6 : "RE",
    }
    return dir_map[d]

  # plot router util;
  def plot_router_util(self, fig, ax, XY_order, cond, title, denom):
    df = self.network_df[self.network_df["XY_order"] == XY_order]
    # filter condition
    df = cond(df)
    # groupby
    group_df        = df.groupby("global_ctr")
    group_idle      = group_df["idle"].sum()
    group_utilized  = group_df["utilized"].sum()
    group_stalled   = group_df["stalled"].sum()
    ts = list(group_df.groups.keys())
    ts.sort()
    # xs
    xs = []
    # ys
    ys_utilized = []
    ys_stalled  = []
    ys_idle     = []
    for i in range(len(ts)-1):
      t0 = ts[i]
      t1 = ts[i+1]
      if t1 < self.end_timestamp:
        xs.append((t0+t1)/2)
        y_utilized = (group_utilized[t1] - group_utilized[t0]) / denom
        y_stalled = (group_stalled[t1] - group_stalled[t0]) / denom
        y_idle = (group_idle[t1] - group_idle[t0]) / denom
        ys_utilized.append(y_utilized)
        ys_stalled.append(y_stalled)
        ys_idle.append(y_idle)
    # stackplot
    labels = ["utilized", "stalled", "idle"]
    colors = ["green", "yellow", "gray"]
    ax.stackplot(xs, ys_utilized, ys_stalled, ys_idle, labels=labels, colors=colors, step="post")
    ax.set_xticks([])
    ax.set_title(title)
    ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5,-0.23))
    ax.set_xlim(xs[0], xs[-1])
    ax.set_ylim(0,100)
    return

# main;
if __name__ == "__main__":
  # arguments;
  test_path = sys.argv[1]
  vis = PeriodicStatVisualizer(test_path)
  plots = ["Core", "Cache", "DRAM", "noc-tile-cache", "noc-fwd-horiz", "noc-fwd-vert", "noc-rev-horiz", "noc-rev-vert"]
  #plots = ["Core", "Cache", "DRAM", ]
  vis.visualize(plots)
