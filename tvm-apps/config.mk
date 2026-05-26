# ════════════════════════════════════════════════════════════════════════════
#  config.mk — user settings for AraXL/tvm-apps/Makefile
#
#  Machine-specific paths (TVM tree, Verilator) go in local.mk
#
#  Command-line overrides always win, e.g.:
#    make sim app=tiny_mlp nr_clusters=8 sim_cycles=20000
# ════════════════════════════════════════════════════════════════════════════

# ─── App ─────────────────────────────────────────────────────────────────────
# Kernel under kernels/ or model under models/ to build/simulate.
app := dotproduct

# ─── Hardware configuration ──────────────────────────────────────────────────
# These settings are baked into the Verilator binary at compile time.
# Changing any of them requires:  make verilate  (then  make sim).
#
# config selects the hardware config file from AraXL/config/<config>.mk
config      := default
nr_clusters := 4
nr_lanes    := 4

# Memory / interconnect latency in cycles (0 = ideal). Requires re-verilate.
mem_latency  := 0
cva6_latency := 0
ring_latency := 0

# ─── Simulation ──────────────────────────────────────────────────────────────
# Simulator backend. Only verilator is wired; vcs is reserved.
simulator := verilator

# Stop the sim after this many simulated cycles (empty = run to program exit).
sim_cycles :=

# Verilator FST waveform tracing.
# Requires a trace-enabled binary built with:  make verilate trace=1
trace := 0

# ─── Build parallelism ───────────────────────────────────────────────────────
verilate_jobs    := 8
verilate_threads := 8

# ─── Tools ───────────────────────────────────────────────────────────────────
# TVM_PYTHON: Python command with the tvm-dev conda env available.
# TVM_HOME, VERILATOR_ROOT: set in local.mk (see local.mk.example).
TVM_PYTHON ?= conda run -n tvm-dev python

# spike-dasm for instruction-trace decoding during sim.
# Defaults to the bundled binary from AraXL/scripts/get-started.sh.
SPIKE_DASM ?= $(ARA_DIR)/install/riscv-isa-sim/bin/spike-dasm
