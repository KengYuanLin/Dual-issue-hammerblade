import pandas as pd
import sys

NUM_TILES_X = 16
NUM_TILES_Y = 8

STALL_CLASSIFIER = {
  "stall_barrier"           : "BarrierStall",
  "stall_bypass"            : "BypassStall",
  "stall_depend_dram_load"  : "MemorySysStall",
  "stall_depend_fdiv"       : "DivStall",
  "stall_depend_local_load" : "BypassStall",
  "stall_fdiv_busy"         : "DivStall",
  "stall_fence"             : "MemorySysStall",
  "stall_remote_req"        : "NetworkStall",
  "bubble_branch_miss"      : "BranchMiss",
}
STALL_CLASSES = {
  "BarrierStall",
  "BypassStall",
  "MemorySysStall",
  "DivStall",
  "NetworkStall",
  "BranchMiss"
}

class PCStallCompression:
  # constructor;
  def __init__(self, bpath):
    self.bpath = bpath
    self.find_start_end_cycle()
    # read trace_df
    self.trace_df = pd.read_csv(self.bpath + "/vanilla_operation_trace.csv")
    self.trace_df["operation"] = self.trace_df["operation"].replace(STALL_CLASSIFIER)
    return

  # find start and end cycle for each core;
  def find_start_end_cycle(self):
    # read stats.csv
    df = pd.read_csv(self.bpath + "/vanilla_stats.csv")
    self.start_cycles = {}
    self.end_cycles   = {}
    for i in range(len(df)):
      xy = (df["x"].iloc[i],  df["y"].iloc[i])
      tag_type = (0xc0000000 & df["tag"].iloc[i]) >> 30
      global_ctr = df["global_ctr"].iloc[i]
      # kernel start;
      if tag_type == 2:
        self.start_cycles[xy] = global_ctr
      # kernel end;
      elif tag_type == 3:
        self.end_cycles[xy] = global_ctr
    #print(len(self.start_cycles))
    #print(len(self.end_cycles))
    return

  def find_true_percentage(self):
    total = 0
    stalls = {}
    for key in STALL_CLASSES:
      stalls[key] = 0

    for x in range(NUM_TILES_X):
      for y in range(NUM_TILES_Y):
        xy = (x,y)
        tdf = self.trace_df[(self.trace_df["x"] == x)
                            & (self.trace_df["y"] == y)
                            & (self.trace_df["cycle"] >= self.start_cycles[xy])
                            & (self.trace_df["cycle"] < self.end_cycles[xy])]
        # total count
        total += len(tdf)
        # stall/bubble counts
        group_df = tdf.groupby(["operation"]).count().reset_index()
        for i in range(len(group_df)):
          op = group_df["operation"].iloc[i]
          count = group_df["cycle"].iloc[i]
          if op in STALL_CLASSES:
            stalls[op] += count
      
    # true stall percentages;
    print("True stall percentages:")
    self.true_stall_pct = {}
    for key in STALL_CLASSES:
      self.true_stall_pct[key] = stalls[key]/total
      print("  {} = {:.2f} %".format(key, self.true_stall_pct[key]*100))
    self.total_stall = total
    return


  # see how much can be compressed
  def analyze_compression(self):
    compressed_dict = {}
    compressed_list = []
    for x in range(NUM_TILES_X):
      for y in range(NUM_TILES_Y):
        xy = (x,y)
        tdf = self.trace_df[(self.trace_df["x"] == x)
                            & (self.trace_df["y"] == y)
                            & (self.trace_df["cycle"] >= self.start_cycles[xy])
                            & (self.trace_df["cycle"] < self.end_cycles[xy])]

        curr_pc = None
        curr_op = None
        curr_count = 0
        for i in range(len(tdf)):
          pc = tdf["pc"].iloc[i]
          op = tdf["operation"].iloc[i]

          if op in STALL_CLASSES:
            # it's one of stalls;
            if curr_pc is None:
              # start a new one;
              curr_pc = pc
              curr_op = op
              curr_count = 1
            else:
              # check if it's a continuation;
              if (curr_pc == pc) and (curr_op == op):
                curr_count += 1
              else:
                # send off curr pc,op
                compressed_list.append((curr_pc,curr_op,curr_count))
                if  (curr_pc,curr_op) in compressed_dict:
                  compressed_dict[(curr_pc,curr_op)] += curr_count
                else:
                  compressed_dict[(curr_pc,curr_op)] = curr_count
                # reset;
                curr_pc = None
                curr_op = None
                curr_count = 0
          else:
            # it's not one of stalls;
            if curr_pc is not None:
              # send off curr pc,op
              compressed_list.append((curr_pc,curr_op,curr_count))
              if  (curr_pc,curr_op) in compressed_dict:
                compressed_dict[(curr_pc,curr_op)] += curr_count
              else:
                compressed_dict[(curr_pc,curr_op)] = curr_count
              # reset;
              curr_pc = None
              curr_op = None
              curr_count = 0
        # do it for the last time;
        if curr_pc is not None:
          # send off curr pc,op
          compressed_list.append((curr_pc,curr_op,curr_count))
          if  (curr_pc,curr_op) in compressed_dict:
            compressed_dict[(curr_pc,curr_op)] += curr_count
          else:
            compressed_dict[(curr_pc,curr_op)] = curr_count
          # reset;
          curr_pc = None
          curr_op = None
          curr_count = 0
     
    print(self.total_stall)
    print(len(compressed_list))
    return

# main();
if __name__ == "__main__":
  bpath = sys.argv[1]
  pcsc = PCStallCompression(bpath)
  pcsc.find_true_percentage()
  pcsc.analyze_compression()
