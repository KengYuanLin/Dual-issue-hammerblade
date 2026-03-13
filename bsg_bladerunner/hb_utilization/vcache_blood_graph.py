import sys
import os
import csv
import pandas as pd
import re
from PIL import Image, ImageDraw, ImageFont, ImageColor


NUM_TILES_Y = 8
NUM_TILES_X = 16
NUM_VCACHE = 32

STALL_COLOR = {
  "idle": "gray",
  "ld_seq_lw": "lime",
  "ld_lw": "green",
  "ld_lh": "green",
  "ld_lhu": "green",
  "ld_lb": "green",
  "ld_lbu": "green",

  "sm_seq_sw": "cyan",
  "sm_sw": "blue",
  "sm_sh": "blue",
  "sm_sb": "blue",

  "stall_rsp": "yellow",
  "miss"   : "lightpink",
  "miss_ld": "lightpink",
  "miss_st": "lightpink",

  "atomic": "purple",
}


class VcacheBloodGraph:
  #constructor
  def __init__(self):
    self.parse_trace()
    self.parse_stats()
    self.stall_color = STALL_COLOR
    return

  def parse_trace(self, trace_file="vcache_operation_trace.csv"):
    traces = []
    with open(trace_file) as f:
      csv_reader = csv.DictReader(f, delimiter=",")
      for row in csv_reader:
        trace = {}
        trace["cycle"] = int(row["cycle"])
        trace["x"] = self.parse_x_cord(row["vcache"])
        trace["y"] = self.parse_y_cord(row["vcache"])
        trace["op"] = row["operation"]
        traces.append(trace)
    self.traces = traces
    return

  def parse_x_cord(self, vcache_name):
    search = re.search("\.vc_x\[(.*)\]", vcache_name)
    if search:
      return int(search.group(1))
    else:
      raise ValueError("x coordinate could not be parsed.")

  def parse_y_cord(self, vcache_name):
    if "north" in vcache_name:
      return 0
    else:
      return 1

  def parse_stats(self, stat_file="vcache_stats.csv"):
    try:
      df = pd.read_csv(stat_file)
    except:
      print("WARNING: {} not found.".format(stat_file))
      return

    tags = df["tag"]
    cycles = df["global_ctr"]

    self.start_cycle = (2**32)-1
    self.end_cycle = 0
    for i in range(len(tags)):
      tag = tags[i]
      cycle = cycles[i]
      tag_type = (0xc0000000 & tag) >> 30
      # kernel start
      if tag_type == 2:
        if self.start_cycle > cycle:
          self.start_cycle = cycle
      # kernel end
      elif tag_type == 3:
        if self.end_cycle < cycle:
          self.end_cycle = cycle
    return

  def init_image(self):
    self.img_width = 2048
    self.img_height = ((self.end_cycle-self.start_cycle+self.img_width)//self.img_width)*(2+(NUM_VCACHE))
    self.img = Image.new("RGB", (self.img_width, self.img_height), "black")
    self.pixel = self.img.load()
    return

  def mark_trace(self, trace):
    cycle = trace["cycle"]
    if cycle < self.start_cycle:
      return
    if cycle > self.end_cycle:
      return

    cycle0 = cycle - self.start_cycle
    col = cycle0 % self.img_width
    floor  = cycle0 // self.img_width
    row = (floor*(2+NUM_VCACHE)) + (trace["x"] + (trace["y"]*NUM_TILES_X))
    assert(row <self.img_height), "Error: Out of height range: {}, {}".format(row, self.img_height)
    
    # color 
    op = trace["op"]
    if op in self.stall_color:
      color_str = self.stall_color[op]
    else:
      print("WARNING: Invalid op = {}".format(op))
      color_str = "black"

    col = int(col)
    row = int(row)
    self.pixel[col,row] = ImageColor.getrgb(color_str)
    return

  def generate_legend(self):
    palette = {}
    palette["idle"] = "gray"
    palette["ld_seq_lw"] = "lime"
    palette["load"] = "green"
    palette["sm_seq_sw"] = "cyan"
    palette["store"] = "blue"
    palette["stall_rsp"] = "yellow"
    palette["miss"] = "lightpink"
    palette["atomic"] = "purple"

    cell_height = 30
    cell_width = 300
    img_height = len(palette.keys()) * cell_height
    img_width = cell_width
    
    i = Image.new("RGB", (img_width,img_height), "black")
    a = ImageDraw.Draw(i)
    curr_idx = 0
    for key in palette.keys():
      y0 = cell_height * curr_idx
      y1 = y0 + cell_height
      x0 = 0 
      x1 = 100
      a.rectangle([x0,y0,x1,y1], fill=ImageColor.getrgb(palette[key]), outline=ImageColor.getrgb("black"))
      a.text((x1+1, y0+10), key, fill=ImageColor.getrgb("white"))
      curr_idx += 1
    i.save("vcache_bg_legend.png")
    return 

  def generate(self):
    self.init_image()
    for trace in self.traces:
      self.mark_trace(trace)

    self.img.save("vcache_bg.png")
    self.img.save("vcache_bg.pdf")
    return

    
# main()
if __name__ == "__main__":
  os.chdir(sys.argv[1])
  bg = VcacheBloodGraph()
  bg.generate_legend()
  bg.generate()
