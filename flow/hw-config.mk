# ════════════════════════════════════════════════════════════════════════════
#  flow/hw-config.mk — shared hardware/run config + simulator-binary naming
#
#  This is the SINGLE source of truth for the RTL-sim binary paths. Every
#  provider (c / tvm / tilelang / prebuilt) includes this, so they all resolve
#  the *identical* Verilator/VCS binary for a given hardware geometry. The
#  binaries are keyed only on (nr_clusters, nr_lanes, latencies, trace) — they
#  are ELF-agnostic, which is exactly why they can be shared across providers.
#
#  Requires (set by the includer or config.mk): ARA_DIR, nr_clusters, nr_lanes,
#  mem_latency, cva6_latency, ring_latency, trace, sim_cycles.
# ════════════════════════════════════════════════════════════════════════════

# ─── Hardware geometry defaults (overridable by config.mk / command line) ────
nr_lanes      ?= 4
nr_clusters   ?= 2
config        ?= default
mem_latency   ?= 0
cva6_latency  ?= 0
ring_latency  ?= 0
trace         ?= 0
sim_cycles    ?=

# Normalize trace into a boolean (1/empty) and a status (1/0 for logs/manifests).
trace_enabled := $(if $(filter 1 true yes on,$(strip $(trace))),1,)
trace_status  := $(if $(trace_enabled),1,0)

# Verilator runtime arg: bound the run to N simulated cycles when sim_cycles set.
SIM_CYCLE_ARG := $(if $(strip $(sim_cycles)),--term-after-cycles=$(sim_cycles),)

# ─── Simulator-binary path naming (the load-bearing convention) ──────────────
# A binary's directory encodes the full hardware config so distinct configs do
# not clobber each other and a matching binary is reused across runs/providers.
_mem_lat_sfx  := $(if $(filter-out 0,$(mem_latency)),-ml$(mem_latency),)
_cva6_lat_sfx := $(if $(filter-out 0,$(cva6_latency)),-cl$(cva6_latency),)
_ring_lat_sfx := $(if $(filter-out 0,$(ring_latency)),-rl$(ring_latency),)
_lat_sfx      := $(_mem_lat_sfx)$(_cva6_lat_sfx)$(_ring_lat_sfx)

VERIL_BUILD_DIR := build-nc$(nr_clusters)-l$(nr_lanes)$(_lat_sfx)$(if $(trace_enabled),-trace,)
VERIL_BINARY    := $(ARA_DIR)/hardware/$(VERIL_BUILD_DIR)/verilator/Vara_tb_verilator

VCS_BUILD_DIR   := build-vcs-nc$(nr_clusters)-l$(nr_lanes)$(_lat_sfx)
VCS_BINARY      ?= $(ARA_DIR)/hardware/$(VCS_BUILD_DIR)/vcs/simv
VCS_DPI_LIB     ?= $(ARA_DIR)/hardware/$(VCS_BUILD_DIR)/work-dpi/ara_dpi

# ─── EDA tool env for VCS/Verdi (inherited from shell or local.mk) ───────────
# Only injected into sub-makes when actually set, so an unset value never
# clobbers the inherited PATH / license.
VERDI    ?= verdi
VCS_ENV  := $(if $(strip $(VCS_HOME)),VCS_HOME=$(VCS_HOME) PATH=$(VCS_HOME)/bin:$$PATH ,)$(if $(strip $(LM_LICENSE_FILE)),LM_LICENSE_FILE=$(LM_LICENSE_FILE) ,)
