# ════════════════════════════════════════════════════════════════════════════
#  flow/config.mk — user settings for the unified orchestrator.
#
#  Machine-specific paths (TVM tree, toolchain) go in local.mk (gitignored).
#  Command-line overrides always win:
#     make sim app=c:fmatmul nr_clusters=4 sim_cycles=20000
# ════════════════════════════════════════════════════════════════════════════

# ─── App ─────────────────────────────────────────────────────────────────────
# Namespaced as  <provider>:<name>  — provider is one of:
#   c:<name>         hand-written AraXL C kernel in apps/<name>/
#   tvm:<name>       TVM kernel/model in tvm-apps/{kernels,models}/<name>/
#   tilelang:<name>  TileLang kernel in tilelang-apps/<name>/   (future provider)
#   prebuilt:<label> any existing ELF — pass elf=<path>
# Run `make list-apps` to see the catalog.
app := c:imatmul

# ─── Hardware configuration (baked into the sim binary; re-verilate on change) ─
# Scale AraXL with nr_clusters (the number of Ara2 clusters). That is the knob
# you change for AraXL.
#
# nr_lanes is the lanes-per-cluster count and should almost always stay 4 — that
# is the AraXL standard. Changeable lane counts are a holdover from the upstream
# Ara/Ara2 repos; AraXL keeps the knob (and the 2/8/16-lane configs exist) but
# 4 is the design point and rarely, if ever, changes. Prefer adding clusters.
config      := default
nr_clusters := 2
# nr_lanes: AraXL standard is 4 — rarely change; scale via nr_clusters instead.
nr_lanes    := 4
mem_latency  := 0
cva6_latency := 0
ring_latency := 0
# gf12_sram=1 builds the VCS sim with the private GF12 VRF SRAM macro (needs
# GF12_SRAM_DIR in hardware/local.mk). Empty/0 = public behavioral tc_sram.
gf12_sram :=

# ─── Simulation ──────────────────────────────────────────────────────────────
# simulator: verilator | vcs
simulator := verilator
# sim_cycles: stop after N simulated cycles (empty = run to program exit)
sim_cycles :=
# trace: Verilator FST tracing; needs a trace binary (`make verilate trace=1`)
trace := 0

# ─── Build parallelism (verilate) ─────────────────────────────────────────────
verilate_jobs    := 8
verilate_threads := 8
