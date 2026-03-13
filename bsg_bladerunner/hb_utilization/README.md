### Introduction

  hb_utilization repo is a collection of python scripts to parse and summarize/visualize HB manycore profiler outputs.


### Requirements

  There are some commonly used python packages required for this: pandas, matplotlib, numpy.


### Commonly used scripts

  Each script should have a comment header that describes how it is used and required inputs.

  - main.py : this is the mainly used script, which summarizes DRAMsim3, vcache, core utilization.

  - periodic_stat.py : this generates temporal utilization graph for core, vcache, DRAM, and network.
