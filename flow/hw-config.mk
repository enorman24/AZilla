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

# ─── Spike (functional ISA-sim) — ONE geometry-independent binary ────────────
# Unlike the Verilator/VCS binaries above (one per hardware geometry), Spike is a
# single RISC-V ISA simulator: it models the ISA, not AraXL's micro-architecture,
# so nr_clusters/latencies are irrelevant to it. Only the --varch vlen and the
# per-(app,config) .spike ELF vary. Spike validates FUNCTIONAL correctness, not
# timing — it emits no cycle counts. Used only by the `c` provider (simulator=spike).
ISA_SIM_INSTALL_DIR ?= $(ARA_DIR)/install/riscv-isa-sim
SPIKE_BIN           ?= $(ISA_SIM_INSTALL_DIR)/bin/spike
# spike-dasm decodes the RTL sim's instruction trace (used by run-sim.sh for any
# simulator); derived from the same dir as SPIKE_BIN.
SPIKE_DASM          ?= $(ISA_SIM_INSTALL_DIR)/bin/spike-dasm
# vlen for spike's --varch, capped at 4096 (spike's max). Mirrors the derivation
# in apps/common/runtime.mk:69 so a flow spike run uses the same vlen as `make
# -C apps spike-run-<name>`. NB: an 8-lane config has vlen=8192 but spike still
# caps at 4096, so a spike PASS at nr_lanes>4 does NOT exercise the RTL's wider
# vector path (surfaced in `show-config`).
# Robust extraction: first 'vlen' assignment line, first integer on it; default
# 4096 if the config file is missing or has no vlen (note ';' not '&&', so the
# echo with the :-4096 fallback runs even when grep matches nothing).
vlen_spike := $(shell vlen=$$(grep -E '^[[:space:]]*vlen' $(ARA_DIR)/config/$(config).mk 2>/dev/null | head -1 | grep -oE '[0-9]+' | head -1); echo "$$(( $${vlen:-4096} < 4096 ? $${vlen:-4096} : 4096 ))")
SPIKE_OPT  ?= --isa=rv64gcv_zfh --varch=vlen:$(vlen_spike),elen:64

# ─── EDA tool env for VCS/Verdi (inherited from shell or local.mk) ───────────
# Only injected into sub-makes when actually set, so an unset value never
# clobbers the inherited PATH / license.
VERDI    ?= verdi
VCS_ENV  := $(if $(strip $(VCS_HOME)),VCS_HOME=$(VCS_HOME) PATH=$(VCS_HOME)/bin:$$PATH ,)$(if $(strip $(LM_LICENSE_FILE)),LM_LICENSE_FILE=$(LM_LICENSE_FILE) ,)
