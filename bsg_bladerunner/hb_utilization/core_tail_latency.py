import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

FILENAME = "vanilla_stats.csv"

XDIM = 16
YDIM = 8

def run():
  try:
    df = pd.read_csv(FILENAME)
  except:
    print("{} not found.".format(FILENAME))
    return

  
  tags = df["tag"]
  global_ctrs = df["global_ctr"]
  xcord = df["x"]
  ycord = df["y"]

  start_cycle = {}
  end_cycle = {}

  for i in range(len(tags)):
    tag = tags[i]
    global_ctr = global_ctrs[i]
    tag_type = (0xc0000000 & tag) >> 30


    key = (xcord[i], ycord[i])

    # kernel start
    if tag_type == 2:
      start_cycle[key] = global_ctr
    # kernel end
    elif tag_type == 3:
      end_cycle[key] = global_ctr

  durations = []
  for y in range(YDIM):
    for x in range(XDIM):
      key = (x,y)
      duration = end_cycle[key] - start_cycle[key] 
      durations.append(duration)
      
  durations.sort()

  #print(durations)

  sorted_keys = list(map(lambda kv: kv[0], sorted(end_cycle.items(), key=lambda kv: kv[1])))
  #print(list(sorted_keys))
  start_sorted = []
  duration_sorted = []
  for sk in sorted_keys:
    start_sorted.append(start_cycle[sk])
    duration_sorted.append(end_cycle[sk] - start_cycle[sk])
  

  fig,ax = plt.subplots()
  fig.set_size_inches(16,7)

  ypos = np.arange(XDIM*YDIM)
  ax.barh(ypos, durations, height=1)
  ax.set_title("Duration for each tile")
  ax.set_xlim(xmax=11000)

  #ax.barh(ypos, duration_sorted, height=1, left=start_sorted)
  #ax.set_title("Start and Finish for each tile")
  #ax.set_xlim(xmax=355000)

  plt.savefig("core_tail_latency.png")
  plt.show()
  

  # create duration map
  duration_map = np.zeros((YDIM,XDIM))
  for y in range(YDIM):
    for x in range(XDIM):
      key = (x,y)
      duration = end_cycle[key] - start_cycle[key] 
      duration_map[y][x] = duration

  np.savetxt("duration.csv", duration_map, delimiter=",")
      
  


if __name__ == "__main__":
  run()
