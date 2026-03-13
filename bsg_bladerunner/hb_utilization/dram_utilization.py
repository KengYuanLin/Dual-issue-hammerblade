import pandas as pd

def parse_dram_stat(filename="blood_graph_stat.log"):
  dram_stat = {}
  try:
    df = pd.read_csv(filename)
  except:
    print("{} not found.".format(filename))
    return

  tags = df["tag"]
  timestamps = df["timestamp"]

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

  # grab start/end df
  start_df = df[df["timestamp"]==start_timestamp].iloc[0]
  end_df   = df[df["timestamp"]==end_timestamp].iloc[0]

  # calculate utilization
  total_cycle = float(end_timestamp - start_timestamp) - float(end_df["refresh"] - start_df["refresh"])
  busy_cycle = float(end_df["busy"] - start_df["busy"])
  read_cycle = float(end_df["read"] - start_df["read"])
  write_cycle = float(end_df["write"] - start_df["write"])
  idle_cycle = total_cycle - busy_cycle - read_cycle - write_cycle

  dram_stat["total"] = total_cycle
  dram_stat["read"]  = read_cycle
  dram_stat["write"] = write_cycle
  dram_stat["busy"]  = busy_cycle
  dram_stat["idle"]  = idle_cycle
  return dram_stat


def print_dram_stat(stat):
  print("--------------------------------")
  print("DRAM Utilization")
  print("--------------------------------")
  print("Read        = {:.2f} %".format(stat["read"]/stat["total"]*100))
  print("Write       = {:.2f} %".format(stat["write"]/stat["total"]*100))
  print("Busy        = {:.2f} %".format(stat["busy"]/stat["total"]*100))
  print("Idle        = {:.2f} %".format(stat["idle"]/stat["total"]*100))
  print("--------------------------------")
  print("Utilization = {:.2f} %".format((stat["read"]+stat["write"])/stat["total"]*100))
  print("Non-Idle    = {:.2f} %".format((stat["read"]+stat["write"]+stat["busy"])/stat["total"]*100))
  print("--------------------------------")
