# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Dual-Issue HammerBlade** project. The goal is to modify the HammerBlade manycore architecture to support dual-issue execution — pairing one integer/memory instruction with one floating-point instruction per cycle — to improve throughput.

The HammerBlade baseline is in `bsg_bladerunner/`. All dual-issue modifications live in:
- `bsg_bladerunner/bsg_manycore/v/vanilla_bean/` — RTL (SystemVerilog)
- `bsg_bladerunner/bsg_replicant/examples/hb_hammerbench/apps/` — kernel benchmarks

## Key Commands

### Run a simulation (VCS cosimulation)
```bash
cd bsg_bladerunner/bsg_replicant/examples/hb_hammerbench/apps/memcpy/tile-x_16__tile-y_8__buffer-size_4096__warm-cache_no
make profile.log
```
`profile.log` contains all simulation output including debug stall messages.

### Force recompile the RTL simulator after RTL changes
After editing any `.sv` file, make should auto-detect the change via timestamps. If it doesn't:
```bash
# Delete the cached simulator binary for the 16x8 profile configuration:
rm -rf bsg_bladerunner/bsg_replicant/machines/pod_X1Y1_ruche_X16Y8_hbm_one_pseudo_channel/bigblade-vcs/profile/simv
```
Then re-run `make profile.log`.

### Run other apps
```bash
cd bsg_bladerunner/bsg_replicant/examples/hb_hammerbench/apps/<appname>/<testdir>
make profile.log
```

## Architecture of Dual-Issue Modifications

### Pipeline Slots
- **Slot 0 (INT)**: `id_n.instruction` / `id_n.decode` — the primary instruction fetched at PC
- **Slot 1 (FP)**: `id_n.instruction1` / `id_n.decode1` — the instruction at PC+1, only issued in dual-issue mode

In `vanilla_core.sv`, `int_instr_n`/`int_decode_n` populate slot 0, and `fp_instr_n`/`fp_decode_general_n` populate slot 1.

### Dual-Issue Control (`vanilla_issue_ctrl.sv`)
Controls `can_issue_dual_o`. Dual-issue is allowed ONLY for FP+INT pairs and is blocked when:
- Any control instruction is involved (branch, jal, jalr, mret, barsend, barrecv, fence, idiv)
- Intra-pair RAW hazard (slot 1 reads a register slot 0 writes)
- Structural port hazard: FP slot reads INT rs1 (`decode1.read_rs1`), writes INT rd (`decode1.write_rd`), or INT slot reads FP registers

### PC Advancement
`safe_dual_issue = 1'b0` is hardcoded — the PC always advances by 1. This means dual-issue is currently effectively disabled (PC never advances by 2). Enable by setting `safe_dual_issue = can_issue_dual` when dual-issue correctness is verified.

### Modified RTL Files
| File | Change |
|------|--------|
| `vanilla_core.sv` | Main pipeline — dual-issue routing, `id_n` struct population, scoreboard/regfile wiring |
| `vanilla_issue_ctrl.sv` | **New** — dual-issue feasibility logic |
| `bsg_vanilla_pkg.sv` | `id_signals_s` struct extended with `instruction1`, `decode1`, `fp_decode1`, etc. |
| `icache.sv` | Added `instr1_o` (PC+1 instruction output), `is_block_boundary_o` |
| `regfile.sv` / `regfile_synth.sv` | Added `num_ws_p` parameter; FP regfile uses `num_ws_p=2` |
| `mcsr.sv` | Added debug `$display` statements only |

## Critical Design Rules for Single-Issue Mode

In single-issue mode (all integer benchmarks like memcpy), `id_n.decode1` / `id_r.decode1` fields are populated from the PC+1 instruction but are **NOT being issued**. Any logic that uses `decode1` signals in single-issue mode introduces bugs.

**The two bugs already fixed:**

1. **Register file read address** (`vanilla_core.sv` ~line 1517):
   `int_rs1_addr` and `int_rs2_addr` must always use `id_n.instruction.rs1/rs2` — never `id_n.instruction1`. Using instruction1's rs1/rs2 causes wrong register reads for every instruction.

2. **Integer scoreboard addresses** (`vanilla_core.sv` ~line 375):
   `int_sb_rs1_addr`, `int_sb_rs2_addr`, `int_sb_rd_addr`, `int_sb_read_rs1/rs2/write_rd` must use `id_r.decode.read_rs1` / `id_r.instruction.rs1` — never `decode1`. Using `decode1` here causes the scoreboard to skip dependency stalls (e.g., for amoadd return values), causing tiles to read stale register values and all tiles to incorrectly enter the barrier sleep loop → deadlock.

**Remaining `decode1`-based logic that causes spurious stalls (performance only, not correctness):**
- `stall_depend_local_load` includes `id1_depend_int_load` (next instruction's load dependency)
- `stall_bypass_fp_rs1` checks `id_r.decode1.read_rs1` against in-flight writes

These are false-positive stalls that self-clear after 1–3 cycles and do not cause deadlocks.

## Barrier Mechanism (Important for Debugging Deadlocks)

`bsg_barrier_tile_group_sync()` uses `bsg_barrier_amoadd` internally:
1. All tiles do `amoadd.w` to a shared counter — the last tile (winner, gets old_value=N-1) skips the sleep loop
2. Non-winner tiles execute `lr.w (addr)` (sets `reserved_r=1`) then `lr.w.aq (addr)` (stalls via `stall_lr_aq`)
3. Winner sends remote STOREs to each sleeping tile's local DMEM at `reserved_addr` → triggers `break_reserve`
4. All tiles then execute hardware `barsend` + `barrecv`

`stall_lr_aq = is_lr_aq_op & (reserved_r | lsu_reserve_lo) & ~break_reserve`
`break_reserve = reserved_r & (reserved_addr_r == dmem_addr_li) & dmem_v_li & dmem_w_li`

## Debug Output

The watchdog in `vanilla_core.sv` fires after 5000 consecutive stall cycles and prints:
```
[DBG][STALL] persistent stall at t=... x=... y=... pc=... stall_id=... stall_all=...
[DBG][STALL][ID]    long=... local=... lr_aq=... barrier=...
[DBG][STALL][LRAQ]  reserved_r=... break_reserve=... reserved_addr=... dmem_v=... dmem_w=...
[DBG][STALL][BARRIER] barrier_i=... barrier_o=...
[DBG][STALL][SB]    int_dep=... float_dep=...
```
To enable debug for a specific tile, set `target_tile_debug` for that tile's coordinates in `vanilla_core.sv`.
