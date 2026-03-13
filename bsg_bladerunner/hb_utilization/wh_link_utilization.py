import pandas as pd

NUM_WH_LINKS = 8
FILENAME = "wh_link_stat.csv"

def parse_wh_link_stat():
  try:
    df = pd.read_csv(FILENAME)
  except:
    print("{} not found.".format(FILENAME))
    return

  tags = df["tag"]
  timestamps = df["global_ctr"]

  # find start and end timestamp
  start_timestamp = (2**32)-1
  end_timestamp = 0
  for i in range(len(tags)):
    tag = tags[i]
    timestamp = timestamps[i]
    tag_type = (0xc0000000 & tag) >> 30

    # kernel start
    if tag_type == 2:
      if start_timestamp > timestamp:
        start_timestamp = timestamp
    # kernel end
    elif tag_type == 3:
      if end_timestamp < timestamp:
        end_timestamp = timestamp


  # calculate cycles
  total_cycle = (float(end_timestamp - start_timestamp) * NUM_WH_LINKS)
  start_input_df  = df[(df["global_ctr"]==start_timestamp) & (df["inout"] == "in")]
  end_input_df    = df[(df["global_ctr"]==end_timestamp)   & (df["inout"] == "in")]
  start_output_df = df[(df["global_ctr"]==start_timestamp) & (df["inout"] == "out")]
  end_output_df   = df[(df["global_ctr"]==end_timestamp)   & (df["inout"] == "out")]


  # assert that you grabbed correctly.
  #print(len(start_input_df["global_ctr"]))
  #print(start_input_df)
  assert len(start_input_df["global_ctr"]) == NUM_WH_LINKS
  assert len(end_input_df["global_ctr"]) == NUM_WH_LINKS
  assert len(start_output_df["global_ctr"]) == NUM_WH_LINKS
  assert len(end_output_df["global_ctr"]) == NUM_WH_LINKS

  input_idle_cycle = float(sum(end_input_df["idle"]) - sum(start_input_df["idle"]))
  input_stall_cycle = float(sum(end_input_df["stall"]) - sum(start_input_df["stall"]))
  input_util_cycle = total_cycle - input_idle_cycle - input_stall_cycle

  output_idle_cycle = float(sum(end_output_df["idle"]) - sum(start_output_df["idle"]))
  output_stall_cycle = float(sum(end_output_df["stall"]) - sum(start_output_df["stall"]))
  output_util_cycle = total_cycle - output_idle_cycle - output_stall_cycle
 
  #print(end_input_df) 
  #print(start_input_df) 
  #print(total_cycle)
  #print(input_idle_cycle)
  #print(input_stall_cycle)
  #print(input_util_cycle)

  print("")
  print("--------------------------------")
  print("WH Link Utilization")
  print("--------------------------------")
  print("(in)  Idle        = {:.2f} %".format(input_idle_cycle   / total_cycle*100))
  print("(in)  Stall       = {:.2f} %".format(input_stall_cycle  / total_cycle*100))
  print("(out) Idle        = {:.2f} %".format(output_idle_cycle  / total_cycle*100))
  print("(out) Stall       = {:.2f} %".format(output_stall_cycle / total_cycle*100))
  print("--------------------------------")
  print("(in)  Utilization = {:.2f} %".format(input_util_cycle   / total_cycle*100))
  print("(out) Utilization = {:.2f} %".format(output_util_cycle  / total_cycle*100))
  print("--------------------------------")
