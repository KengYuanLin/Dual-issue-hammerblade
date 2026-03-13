#
#   main.py
#
#   This script summarizes DRAMsim3, vcache, and vanilla core stats.
#   
#   Input files:
#   - blood_graph_stat.log
#   - vcache_stats.csv
#   - vanilla_stats.csv
# 
#   How to use:
#   python main.py {path-to-input-files}   
#

import dram_utilization as dr
import vcache_utilization as vc
import core_utilization as core
import wh_link_utilization as wh
#import router_utilization as rtr

import os
import sys

os.chdir(sys.argv[1])

dram_stat = dr.parse_dram_stat()
dr.print_dram_stat(dram_stat)

vc_stat = vc.parse_vcache_stat()
if vc_stat is not None:
  vc.print_vcache_stat(vc_stat)

core_stat = core.parse_vanilla_stat()
if core_stat is not None:
  core.print_vanilla_stat(core_stat)
#core.summarize_core_stall(core_stat)

#wh.parse_wh_link_stat()
#rtr.parse_router_stat()
