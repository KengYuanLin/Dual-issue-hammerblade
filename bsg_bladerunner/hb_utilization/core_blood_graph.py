import sys
import os
import csv
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageColor

NUM_TILES_Y = 8
NUM_TILES_X = 16

DETAILED_STALL_BUBBLE_COLOR = {
  # DRAM = red
  "stall_depend_dram_load"        : "yellow",
  "stall_depend_dram_seq_load"    : "yellow",
  "stall_depend_dram_amo"         : "darkred",

  # TG
  "stall_depend_group_load"   : "navy",
  "stall_depend_global_load"  : "navy",
                              
  # fdiv, idiv      
  "stall_depend_idiv"         : "magenta",
  "stall_depend_fdiv"         : "magenta",
  "stall_fdiv_busy"           : "magenta",
  "stall_idiv_busy"           : "magenta",

  # network = orange
  "stall_remote_req"          : "orange",
  #"stall_remote_credit"       : "darkorange",
  "stall_remote_credit"       : "orange",

  # memory ordering = 
  "stall_amo_aq"              : "dimgray",
  "stall_amo_rl"              : "dimgray",
  "stall_fence"               : "dimgray",
   
  # barrier
  "stall_barrier"             : "gray",
  "stall_lr_aq"               : "dimgray",

  # yellow
  "stall_depend_local_load"   : "yellow",
  "stall_depend_imul"         : "yellow",
  "stall_bypass"              : "yellow",
  "stall_fcsr"                : "yellow",
  
  # remote write back
  "stall_remote_flw_wb"       : "yellow",
  "stall_remote_ld_wb"        : "yellow",
                                     
  # branch = purple
  "bubble_branch_miss"        : "purple",
  "bubble_jalr_miss"          : "purple",

  # icache
  "icache_miss"               : "cyan",
  "bubble_icache_miss"        : "cyan",
  "stall_ifetch_wait"         : "cyan",
}

INSTR_LIST = [
  "local_ld", "local_st",
  "remote_ld_dram",
  "remote_ld_global",
  "remote_ld_group",
  "remote_st_dram",
  "remote_st_global",
  "remote_st_group",
  "local_flw", "local_fsw",
  "remote_flw_dram",
  "remote_flw_global",
  "remote_flw_group",
  "remote_fsw_dram",
  "remote_fsw_global",
  "remote_fsw_group",
  "lr", "lr_aq",
  "amoswap", "amoor", "amoadd", 
  "beq", "bne",
  "blt", "bge", "bltu", "bgeu",
  "jal", "jalr",
  "sll", "slli", "srl", "srli", "sra", "srai", 
  "add", "addi", "sub",      
  "lui", "auipc",
  "xor", "xori", "or", "ori", "and", "andi",    
  "slt", "slti", "sltu", "sltiu",  
  "div", "divu", "rem", "remu",    
  "mul",      
  "fence",  
  "csrrw", "csrrs", "csrrc", "csrrwi", "csrrsi", "csrrci",
  "barsend", "barrecv",
]

FP_INSTR_LIST = [
  "fadd", "fsub", "fmul",
  "fsgnj", "fsgnjn", "fsgnjx",
  "fmin", "fmax",
  "fcvt_s_w", "fcvt_s_wu", "fmv_w_x",
  "fcvt_w_s", "fcvt_wu_s", "fmv_x_w",
  "fmadd", "fmsub", "fnmsub", "fnmadd",
  "feq", "flt", "fle", "fclass",
  "fdiv", "fsqrt"
]

# Vanilla Core blood_graph
class CoreBloodGraph:
  #constructor
  def __init__(self):
    self.parse_trace()
    self.parse_stats()
    self.stall_bubble_color = DETAILED_STALL_BUBBLE_COLOR
    return

  # parse operation traces csv;
  def parse_trace(self, trace_file="vanilla_operation_trace.csv"):
    traces = []
    with open(trace_file) as f:
      csv_reader = csv.DictReader(f, delimiter=",")
      for row in csv_reader:
        trace = {}
        trace["x"] = int(row["x"])
        trace["y"] = int(row["y"])
        trace["operation"] = row["operation"]
        trace["cycle"] = int(row["cycle"])
        traces.append(trace)
    self.traces = traces
    return

  # parse vanilla stat for start and end cycles;
  def parse_stats(self, stat_file="vanilla_stats.csv"):
    # find start and end cycle for each tile;
    self.start_cycles = {}
    self.end_cycles   = {}

    # default start, end;
    for y in range(NUM_TILES_Y):
      for x in range(NUM_TILES_X):
        key = (x,y)
        self.start_cycles[key] = 0
        self.end_cycles[key] = (2**32)-1

    try:
      df = pd.read_csv(stat_file)
    except:
      print("WARNING: {} not found.".format(stat_file))
      # create default start/end cycles;
      return

    tags = df["tag"]
    cycles = df["global_ctr"]
    xs = df["x"]
    ys = df["y"]
    start_count = 0
    end_count = 0
    self.max_cycle = 0
    self.min_cycle = (2**32)-1

    for i in range(len(tags)):
      tag = tags[i]
      cycle = cycles[i]
      key = (xs[i]-NUM_TILES_X, ys[i]-NUM_TILES_Y)
      tag_type = (0xc0000000 & tag) >> 30
    
      # kernel start
      if tag_type == 2:
        self.start_cycles[key] = cycle
        if cycle < self.min_cycle:
          self.min_cycle = cycle
        start_count += 1
      # kernel end
      elif tag_type== 3:
        self.end_cycles[key] = cycle
        if cycle > self.max_cycle:
          self.max_cycle = cycle
        end_count += 1

    assert(start_count == end_count)
    return


  # init image
  def init_image(self):
    self.img_width = 2048
    self.img_height = ((self.max_cycle-self.min_cycle+self.img_width)//self.img_width)*(2+(NUM_TILES_Y*NUM_TILES_X))
    self.img = Image.new("RGB", (self.img_width, self.img_height), "black")
    self.pixel = self.img.load()
    return


  # mark trace on image;
  def mark_trace(self, trace):
    key = (trace["x"], trace["y"])
    cycle = trace["cycle"]

    # check cycle range
    if cycle < self.start_cycles[key]:
      return
    if cycle > self.end_cycles[key]:
      return
      
    # pixel location
    cycle0 = cycle - self.min_cycle
    if cycle0 < 0:
      return
    col = cycle0 % self.img_width
    floor = cycle0 // self.img_width
    row = floor*(2+(NUM_TILES_X*NUM_TILES_Y)) + (trace["x"]+(trace["y"]*NUM_TILES_X))
    
    assert(row <= self.img_height), "{}, {}".format(row, self.img_height)
    # color
    op = trace["operation"]
    if op in self.stall_bubble_color.keys():
      color_str = self.stall_bubble_color[op]
    elif op in INSTR_LIST:
      color_str = "green"
    elif op in FP_INSTR_LIST:
      color_str = "darkgreen"
    else:
      print("WARNING: Invalid op = {}".format(op))
      color_str = "black"

    # set color on pixel;
    col = int(col)
    row = int(row)
    self.pixel[col,row] = ImageColor.getrgb(color_str)
    return


  # generate image
  def generate(self):
    # init image;
    self.init_image()

    # mark traces;
    for trace in self.traces:
      self.mark_trace(trace)

    # save image;
    self.img.save("core_bg.png")
    self.img.save("core_bg.pdf")
    return

  def generate_legend(self):
    palette = {}
    for key in self.stall_bubble_color:
      palette[key] = self.stall_bubble_color[key]
    palette["int_instr"] = "green"
    palette["fp_instr"] = "darkgreen"

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
    i.save("core_bg_legend.png")
    return

# main()
if __name__ == "__main__":
  os.chdir(sys.argv[1])
  bg = CoreBloodGraph()
  bg.generate_legend()
  bg.generate()
