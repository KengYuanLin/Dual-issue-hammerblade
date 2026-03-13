import dram_utilization as dr
import vcache_utilization as vc
import core_utilization as core
from bisection_util import *

import os
import sys

os.chdir(sys.argv[1])
rf_x = int(sys.argv[2])
num_tiles_x = int(sys.argv[3])
num_tiles_y = int(sys.argv[4])
num_pods_x = int(sys.argv[5])


core_stat = core.parse_vanilla_stat()

# runtime;
print("runtime            = {}".format(core_stat["runtime"]))

# core util;
print("core util          = {:.2f}".format(core_stat["util_pct"]))

# memory sys stall;
dram_stall = core_stat["stall_depend_dram_load"]
dram_stall += core_stat["stall_depend_dram_seq_load"]
dram_stall += core_stat["stall_depend_dram_amo"]
dram_stall += core_stat["stall_amo_aq"]
dram_stall += core_stat["stall_amo_rl"]
dram_stall = dram_stall / core_stat["total_cycle"] * 100
print("MemorySysStall     = {:.2f}".format(dram_stall))

# network stall;
network_stall = core_stat["stall_remote_req"]
network_stall += core_stat["stall_remote_ld_wb"]
network_stall += core_stat["stall_remote_flw_wb"]
network_stall += core_stat["stall_remote_credit"]
network_stall += core_stat["stall_depend_group_load"]
network_stall = network_stall / core_stat["total_cycle"] * 100
print("NetworkStall       = {:.2f}".format(network_stall))

# cache miss rate;
vc_stat = vc.parse_vcache_stat()
print("CacheMissRate      = {:.2f}".format(vc_stat["miss_rate"]))

# dram util;
dram_stat = dr.parse_dram_stat()
print("DRAM Util          = {:.2f}".format((dram_stat["read"]+dram_stat["write"])/dram_stat["total"]*100))

# bisection stall;
bi = BisectionBW("router_stat.csv", rf_x, num_tiles_x, num_tiles_y, num_pods_x)
bi_stat = bi.parse()
print("Bisection stalled  = {:.2f}".format(bi_stat["stalled"]))
