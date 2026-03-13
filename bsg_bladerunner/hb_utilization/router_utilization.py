import pandas as pd
import router_traffic_visualizer as rtv

POD_ORIGIN_X = 16
POD_ORIGIN_Y = 8
FILENAME = "router_stat.csv"

def convert_dir(d):
  if d == 0:
    return "P"
  elif d == 1:
    return "W"
  elif d == 2:
    return "E"
  elif d == 3:
    return "N"
  elif d == 4:
    return "S"
  elif d == 5:
    return "RW"
  elif d == 6:
    return "RE"
  else:
    return "X"


def parse_router_stat():
  try:
    df = pd.read_csv(FILENAME)
  except:
    print("{} not found.".format(FILENAME))
    return

  #tags = df["tag"]
  timestamps = df["global_ctr"]

  # find start and end timestamp
  start_timestamp = (2**32)-1
  end_timestamp = 0
  for i in range(len(timestamps)):
    #tag = tags[i]
    timestamp = timestamps[i]
    #tag_type = (0xc0000000 & tag) >> 30

    # kernel start
    #if tag_type == 2:
    if start_timestamp > timestamp:
      start_timestamp = timestamp
    # kernel end
    #elif tag_type == 3:
    if end_timestamp < timestamp:
      end_timestamp = timestamp
  
  # filter
  df = df[(df["y"] >= POD_ORIGIN_Y-1) & (df["y"] <= POD_ORIGIN_Y+8) ]
  # modify xy
  df["x"] = df["x"].subtract(POD_ORIGIN_X)
  df["y"] = df["y"].subtract(POD_ORIGIN_Y)
  df["output_dir"] = df.apply(lambda x: convert_dir(x.output_dir), axis = 1)

  # calculate cycles
  total_cycle = (float(end_timestamp - start_timestamp))
  fwd_start_df = df[(df["global_ctr"]==start_timestamp) & (df["XY_order"] == 1)]
  fwd_end_df   = df[(df["global_ctr"]==end_timestamp) & (df["XY_order"] == 1)]
  rev_start_df = df[(df["global_ctr"]==start_timestamp) & (df["XY_order"] == 0)]
  rev_end_df   = df[(df["global_ctr"]==end_timestamp) & (df["XY_order"] == 0)]

  # make empty data fram
  fwd_diff_df = df.iloc[:0].copy()
  rev_diff_df = df.iloc[:0].copy()
  del fwd_diff_df["timestamp"]
  del fwd_diff_df["global_ctr"]
  del fwd_diff_df["XY_order"]
  del rev_diff_df["timestamp"]
  del rev_diff_df["global_ctr"]
  del rev_diff_df["XY_order"]

  # calculate diff of idle,utilized,stalled,arbitrated
  # fwd
  for i in range(len(fwd_start_df.index)):
    start_stat = fwd_start_df.iloc[i]
    x = start_stat["x"]
    y = start_stat["y"]
    output_dir = start_stat["output_dir"]
    # find matching stat in end
    end_stat = fwd_end_df[(fwd_end_df["x"] == x) & (fwd_end_df["y"] == y) & (fwd_end_df["output_dir"] == output_dir)].iloc[0]
    idle_diff = end_stat["idle"] - start_stat["idle"]
    utilized_diff = end_stat["utilized"] - start_stat["utilized"]
    stalled_diff = end_stat["stalled"] - start_stat["stalled"]
    arbitrated_diff = end_stat["arbitrated"] - start_stat["arbitrated"]
    # insert a row
    fwd_diff_df = fwd_diff_df.append({
      "x":  x,
      "y":  y,
      "output_dir":  output_dir,
      "idle": idle_diff,
      "utilized":utilized_diff,
      "stalled": stalled_diff,
      "arbitrated": arbitrated_diff
    }, ignore_index=True)

  # rev
  for i in range(len(rev_start_df.index)):
    start_stat = rev_start_df.iloc[i]
    x = start_stat["x"]
    y = start_stat["y"]
    output_dir = start_stat["output_dir"]
    # find matching stat in end
    end_stat = rev_end_df[(rev_end_df["x"] == x) & (rev_end_df["y"] == y) & (rev_end_df["output_dir"] == output_dir)].iloc[0]
    idle_diff = end_stat["idle"] - start_stat["idle"]
    utilized_diff = end_stat["utilized"] - start_stat["utilized"]
    stalled_diff = end_stat["stalled"] - start_stat["stalled"]
    arbitrated_diff = end_stat["arbitrated"] - start_stat["arbitrated"]
    # insert a row
    rev_diff_df = rev_diff_df.append({
      "x":  x,
      "y":  y,
      "output_dir":  output_dir,
      "idle": idle_diff,
      "utilized":utilized_diff,
      "stalled": stalled_diff,
      "arbitrated": arbitrated_diff
    }, ignore_index=True)

  # convert to percentage
  fwd_diff_df["idle"] = fwd_diff_df.apply(lambda x: float(x.idle/total_cycle)*100,axis=1)
  fwd_diff_df["utilized"] = fwd_diff_df.apply(lambda x: float(x.utilized/total_cycle)*100,axis=1)
  fwd_diff_df["stalled"] = fwd_diff_df.apply(lambda x: float(x.stalled/total_cycle)*100,axis=1)
  fwd_diff_df["arbitrated"] = fwd_diff_df.apply(lambda x: float(x.arbitrated/total_cycle)*100,axis=1)
  rev_diff_df["idle"] = rev_diff_df.apply(lambda x: float(x.idle/total_cycle)*100,axis=1)
  rev_diff_df["utilized"] = rev_diff_df.apply(lambda x: float(x.utilized/total_cycle)*100,axis=1)
  rev_diff_df["stalled"] = rev_diff_df.apply(lambda x: float(x.stalled/total_cycle)*100,axis=1)
  rev_diff_df["arbitrated"] = rev_diff_df.apply(lambda x: float(x.arbitrated/total_cycle)*100,axis=1)

  NWORST = 5
  fwd_most_stalled = fwd_diff_df.sort_values(by = "stalled", ascending=False).head(NWORST)
  fwd_most_utilized = fwd_diff_df.sort_values(by = "utilized", ascending=False).head(NWORST)
  fwd_most_arbitrated = fwd_diff_df.sort_values(by = "arbitrated", ascending=False).head(NWORST)
  rev_most_stalled = rev_diff_df.sort_values(by = "stalled", ascending=False).head(NWORST)
  rev_most_utilized = rev_diff_df.sort_values(by = "utilized", ascending=False).head(NWORST)
  rev_most_arbitrated = rev_diff_df.sort_values(by = "arbitrated", ascending=False).head(NWORST)

  # change float print format
  pd.options.display.float_format = '{:,.2f}'.format
  
  print("")
  print("--------------------------------")
  print("Router Utilization")
  print("--------------------------------")
  print("FWD most stalled:")
  print(fwd_most_stalled)
  print("FWD most utilized:")
  print(fwd_most_utilized)
  print("FWD most arbitrated:")
  print(fwd_most_arbitrated)
  print("REV most stalled:")
  print(rev_most_stalled)
  print("REV most utilized:")
  print(rev_most_utilized)
  print("REV most arbitrated:")
  print(rev_most_arbitrated)
  print("--------------------------------")

  #print(start_timestamp)
  #print(end_timestamp)

  rtv.visualize_router_traffic(fwd_diff_df, "stalled", "fwd_stalled.png")
  rtv.visualize_router_traffic(fwd_diff_df, "utilized", "fwd_utilized.png")
  rtv.visualize_router_traffic(rev_diff_df, "stalled", "rev_stalled.png")
  rtv.visualize_router_traffic(rev_diff_df, "utilized", "rev_utilized.png")

