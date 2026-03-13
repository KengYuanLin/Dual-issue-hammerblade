import sys
import os
import pandas as pd
import matplotlib.pyplot as plt


ROUTER_PERIOD=250
NUM_TILES_Y = 8
NUM_TILES_X = 32


SCALE  = 2.0
WIDTH  = 8.0*SCALE
HEIGHT = 2.0*SCALE

class BisectionTransfer:
  # constructor;
  def __init__(self, app_path, num_plots_y):
    self.num_plots_y = num_plots_y
    self.app_path = app_path

    # setup fig;
    self.fig, self.ax = plt.subplots(num_plots_y,1)
    self.fig.set_size_inches(WIDTH,HEIGHT)
    return

  # plot;
  def plot_fwd(self, plot_num, test_name, rf_x):
    csv_path = app_path + test_name + "/router_periodic_stat.csv"
    df = pd.read_csv(csv_path)
    df["global_ctr"] = df["global_ctr"].subtract(min(df["global_ctr"]))
    df["x"] = df["x"].subtract(NUM_TILES_X)
    df["y"] = df["y"].subtract(NUM_TILES_Y)
    df["output_dir"] = df.apply(lambda x: self.convert_dir(x.output_dir), axis=1)

    # fwd network
    df = df[df["XY_order"] == 1]

    # select bisection links going East;
    def cond(df):
      cond = (df["output_dir"] == "E") & (df["x"] == ((NUM_TILES_X/2)-1))
      for i in range(rf_x):
        cond |= (df["output_dir"] == "RE") & (df["x"] == ((NUM_TILES_X/2)-1-i))
      return df[cond]
    df = cond(df)
    # groupby;
    group_df = df.groupby("global_ctr")
    group_idle = group_df["idle"].sum()
    group_utilized = group_df["utilized"].sum()
    group_stalled = group_df["stalled"].sum()
    ts = list(group_df.groups.keys())
    ts.sort()
  
    # denom;
    denom = ROUTER_PERIOD * (1+rf_x) * NUM_TILES_Y / 100
  
    # xs;
    xs = []

    # ys
    ys_utilized = []
    ys_stalled = []
    ys_idle = []
    for i in range(len(ts)-1):
      t0 = ts[i]
      t1 = ts[i+1]
      if t1 < 10000000:
        xs.append((t0+t1)/2)
        y_utilized = (group_utilized[t1] - group_utilized[t0]) / denom
        y_stalled = (group_stalled[t1] - group_stalled[t0]) / denom
        y_idle = (group_idle[t1] - group_idle[t0]) / denom
        ys_utilized.append(y_utilized)
        ys_stalled.append(y_stalled)
        ys_idle.append(y_idle)

    # stack plot
    labels = ["utilized", "stalled", "idle"]
    colors = ["green", "yellow", "gray"]
    self.ax[plot_num].stackplot(xs, ys_utilized, ys_stalled, ys_idle, labels=labels, colors=colors, step="post")
    #self.ax[plot_num].set_xticks([])
    #self.ax[plot_num].set_title(title)
    #self.ax[plot_num].legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5,-0.23))

  # plot;
  def plot_rev(self, plot_num, test_name, rf_x):
    csv_path = app_path + test_name + "/router_periodic_stat.csv"
    df = pd.read_csv(csv_path)
    df["x"] = df["x"].subtract(NUM_TILES_X)
    df["y"] = df["y"].subtract(NUM_TILES_Y)
    df["global_ctr"] = df["global_ctr"].subtract(min(df["global_ctr"]))
    df["output_dir"] = df.apply(lambda x: self.convert_dir(x.output_dir), axis=1)

    # rev network
    df = df[df["XY_order"] == 0]

    # select bisection links going West;
    def cond(df):
      cond = (df["output_dir"] == "W") & (df["x"] == ((NUM_TILES_X/2)))
      for i in range(rf_x):
        cond |= (df["output_dir"] == "RW") & (df["x"] == ((NUM_TILES_X/2)+i))
      return df[cond]
    df = cond(df)
    # groupby;
    group_df = df.groupby("global_ctr")
    group_idle = group_df["idle"].sum()
    group_utilized = group_df["utilized"].sum()
    group_stalled = group_df["stalled"].sum()
    ts = list(group_df.groups.keys())
    ts.sort()
  
    # denom;
    denom = ROUTER_PERIOD * (1+rf_x) * NUM_TILES_Y / 100
  
    # xs;
    xs = []

    # ys
    ys_utilized = []
    ys_stalled = []
    ys_idle = []
    for i in range(len(ts)-1):
      t0 = ts[i]
      t1 = ts[i+1]
      if t1 < 10000000:
        xs.append((t0+t1)/2)
        y_utilized = (group_utilized[t1] - group_utilized[t0]) / denom
        y_stalled = (group_stalled[t1] - group_stalled[t0]) / denom
        y_idle = (group_idle[t1] - group_idle[t0]) / denom
        ys_utilized.append(y_utilized)
        ys_stalled.append(y_stalled)
        ys_idle.append(y_idle)

    # stack plot
    labels = ["utilized", "stalled", "idle"]
    colors = ["green", "yellow", "gray"]
    self.ax[plot_num].stackplot(xs, ys_utilized, ys_stalled, ys_idle, labels=labels, colors=colors, step="post")



  def show(self):
    self.fig.tight_layout(pad=0.0)
    plt.show()


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





if __name__ == "__main__":
  app_path = sys.argv[1] 
  bt = BisectionTransfer(app_path, 2)
  bt.plot_fwd(0, "credit_16__len_1", 3)
  bt.plot_rev(1, "credit_16__len_1", 3)
  #bt.plot(1, "credit_32__len_16", 3)
  bt.show()
