SHELL := /usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════════
#  flow/Makefile — the single build+sim orchestrator for AraXL.
#
#  An app is  <provider>:<name>  (c:fmatmul, tvm:fdotproduct, prebuilt:<label>).
#  flow resolves/builds the ELF for that provider, then runs it through ONE
#  shared layer (scripts/run-sim.sh) on ONE shared sim binary — so every
#  provider gets the same run UX on verilator | vcs | spike. Source collections
#  stay in apps/ and tvm-apps/; flow only references them via $(ARA_DIR).
#
#  Include order is load-bearing (each step defines what the next consumes):
#    config.mk          user knobs
#    local.mk           machine paths (gitignored; optional)
#    hw-config.mk       derived geometry + sim-binary paths (SPIKE_BIN/VCS_BINARY/…)
#    providers/<p>.mk   sets ELF + provider-build (+ FLOW_BUILT and build vars)
#    build.mk           shared link→ELF — only when a provider sets FLOW_BUILT
#    sim-run.mk         the `sim` target
#    targets.mk         verilate/compile-vcs + inspection / results / cleanup
# ════════════════════════════════════════════════════════════════════════════

FLOW_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
# flow/ always sits directly under the repo root, so derive it from our own path
# (no git needed — works from a tarball). `make ARA_DIR=…` still overrides.
ARA_DIR  := $(abspath $(FLOW_DIR)/..)
ifeq ($(wildcard $(ARA_DIR)/apps),)
$(error flow: cannot find the AZilla repo root (no apps/ under '$(ARA_DIR)'). Run flow inside an AZilla checkout, or pass ARA_DIR=<repo root>.)
endif

include $(FLOW_DIR)/config.mk
-include $(FLOW_DIR)/local.mk
include $(FLOW_DIR)/hw-config.mk

app       ?= tvm:fdotproduct
simulator ?= verilator
ifndef RUN_ID
RUN_ID := $(shell date +%Y%m%d_%H%M%S)
endif
# config.mk allows trailing `# comments`; strip the space make keeps before them.
app       := $(strip $(app))
simulator := $(strip $(simulator))

# app = <provider>:<name>   (tvm:fdotproduct -> provider=tvm, name=fdotproduct)
provider := $(firstword $(subst :, ,$(app)))
name     := $(patsubst $(provider):%,%,$(app))
APP_SLUG := $(subst :,/,$(app))

# Per-run output tree — flow owns build/ and never writes into the source dirs.
FLOW_BUILD      := $(FLOW_DIR)/build
APP_DIR         := $(FLOW_BUILD)/$(APP_SLUG)
APP_OBJ_DIR     := $(APP_DIR)/01_cross
APP_BIN_DIR     := $(APP_DIR)/02_link
APP_SIM_DIR     := $(APP_DIR)/03_sim
APP_SIM_RUN_DIR := $(APP_SIM_DIR)/runs/$(RUN_ID)
APP_LOG_DIR     := $(APP_DIR)/logs/$(RUN_ID)

# ─── Tooling (override in local.mk) ───────────────────────────────────────────
# TVM_PYTHON: only the tvm: provider needs it (IR generation).
TVM_PYTHON       ?= conda run -n tvm-dev python
# ARTIFACTS_PYTHON: runs the run-management tool (manifests/ledger/status/report).
# It is pure-stdlib there, so a plain python3 works — c:/prebuilt: need no TVM.
ARTIFACTS_PYTHON ?= python3
VERILATOR_ROOT   ?= $(ARA_DIR)/install/verilator
# SPIKE_BIN / SPIKE_DASM / SPIKE_OPT are defined in hw-config.mk (one place for spike).
RUN_SIM          := $(FLOW_DIR)/scripts/run-sim.sh
RETURN_STATUS    := $(ARA_DIR)/hardware/scripts/return_status.sh
verilate_jobs    ?= 8
verilate_threads ?= 8
# Run-management tooling owned by flow (live monitor + manifest/ledger/report).
# flow is the source of truth for these; tvm-apps consumes the same copies.
MONITOR          := $(FLOW_DIR)/scripts/sim-monitor.sh
ARTIFACTS        := $(FLOW_DIR)/scripts/artifacts.py

# TVM tree (tvm: provider only). Default = sibling <repo>/../tools/tvm; set in local.mk.
TVM_HOME         ?= $(ARA_DIR)/../tools/tvm
TVM_LIBRARY_PATH ?= $(TVM_HOME)/build/lib
TVM_PYTHONPATH   ?= $(TVM_HOME)/python
TVM_MANIFEST_ENV := PYTHONPATH=$(ARA_DIR)/tvm-apps:$(TVM_PYTHONPATH):$$PYTHONPATH TVM_HOME=$(TVM_HOME) TVM_LIBRARY_PATH=$(TVM_LIBRARY_PATH)

# Results ledger (durable + gitignored; survives distclean).
RESULTS_DIR := $(FLOW_DIR)/results
LEDGER      := $(RESULTS_DIR)/ledger.jsonl
NOTES       := $(RESULTS_DIR)/notes.json
META        := $(RESULTS_DIR)/meta.json
RESULTS_MD  := $(FLOW_DIR)/RESULTS.md

# Codegen target ABI (matches tvm-apps).
TARGET_TRIPLE := riscv64-unknown-elf
TARGET_MATTR  := +v,+m,+f,+d
TARGET_ABI    := lp64d

# The sim binary that actually ran (recorded in the manifest).
SIM_BINARY := $(if $(filter spike,$(simulator)),$(SPIKE_BIN),$(if $(filter vcs,$(simulator)),$(VCS_BINARY),$(VERIL_BINARY)))

# ─── Build-provenance command templates (artifacts.py) ────────────────────────
# Used by tvm.mk's provider-build and the audit target. Deferred (=) so provider
# vars (TVM_LL, RISCV_CC, LINK_LD, …) resolve at use time, after build.mk loads.
APP_MANIFEST_CMD = $(ARTIFACTS_PYTHON) $(ARTIFACTS) app-manifest \
  --output "$(APP_DIR)/manifest.json" --app "$(app)" --app-kind "$(APP_KIND)" \
  --generator "$(GENERATOR_PY)" --main-c "$(BUILD_MAIN_C)" \
  $(foreach d,$(BUILD_KERNEL_DEPS),--kernel-dep "$(d)") \
  --target-triple "$(TARGET_TRIPLE)" --target-mattr "$(TARGET_MATTR)" --target-abi "$(TARGET_ABI)" \
  --config "$(config)" --nr-clusters "$(nr_clusters)" --nr-lanes "$(nr_lanes)" \
  --mem-latency "$(mem_latency)" --cva6-latency "$(cva6_latency)" --ring-latency "$(ring_latency)" \
  --trace "$(trace_status)" \
  --tool "RISCV_CC=$(RISCV_CC)" --tool "TVM_PYTHON=$(TVM_PYTHON)" --tool "VERILATOR_BINARY=$(VERIL_BINARY)" \
  --app-dir "$(APP_DIR)" --ir-dir "$(TVM_IR_DIR)" --tvm-dir "$(TVM_FINAL_DIR)" \
  --obj-dir "$(APP_OBJ_DIR)" --bin-dir "$(APP_BIN_DIR)" --sim-dir "$(APP_SIM_DIR)" \
  --elf "$(ELF)" --llvm-ir "$(TVM_LL)" --compat-llvm-ir "$(TVM_COMPAT)" \
  --linker-script "$(LINK_LD)" --verilator-binary "$(VERIL_BINARY)"

APP_AUDIT_CMD = $(ARTIFACTS_PYTHON) $(ARTIFACTS) audit \
  --app "$(app)" --app-kind "$(APP_KIND)" --generator "$(GENERATOR_PY)" --main-c "$(BUILD_MAIN_C)" \
  --app-dir "$(APP_DIR)" --ir-dir "$(TVM_IR_DIR)" --tvm-dir "$(TVM_FINAL_DIR)" \
  --obj-dir "$(APP_OBJ_DIR)" --bin-dir "$(APP_BIN_DIR)" --sim-dir "$(APP_SIM_DIR)" \
  --elf "$(ELF)" --llvm-ir "$(TVM_LL)" --compat-llvm-ir "$(TVM_COMPAT)" \
  --linker-script "$(LINK_LD)" --verilator-binary "$(VERIL_BINARY)"

ENV_SNAPSHOT_CMD = $(TVM_MANIFEST_ENV) $(TVM_PYTHON) $(ARTIFACTS) env-snapshot \
  --output "$(APP_BIN_DIR)/env.json" --riscv-cc "$(RISCV_CC)" --git-dir "$(FLOW_DIR)"

# ─── Policy: simulator=spike is c-provider only ───────────────────────────────
# Spike runs a GCC+HTIF .spike ELF; tvm/prebuilt ELFs exit via the RTL eoc path,
# not HTIF, so Spike can't run them. Goal-scoped so inspection targets still work.
_GOALS := $(if $(MAKECMDGOALS),$(MAKECMDGOALS),sim)
ifeq ($(simulator),spike)
ifneq ($(provider),c)
ifneq ($(filter sim provider-build,$(_GOALS)),)
$(error flow: simulator=spike supports only c:<name> apps (got '$(app)'). Use simulator=verilator|vcs, or a c: app — see 'make list-apps')
endif
endif
endif

# Bare `make` prints help and builds nothing (otherwise it would run the first
# target — provider-build — and build the default app, creating build/ dirs).
.DEFAULT_GOAL := help

.PHONY: sim provider-build verilate compile-vcs view-sim report tvm-ir audit \
        show-config list-binaries list-apps list-configs monitor monitor-latest help \
        clean-sim clean-build distclean check-symbols status

# ─── Provider dispatch: one providers/<provider>.mk per provider (additive) ───
ifeq ($(wildcard $(FLOW_DIR)/providers/$(provider).mk),)
  ELF :=
provider-build:
	@echo "ERROR: unknown provider '$(provider)' in app='$(app)'"; \
	 echo "       available: $(patsubst $(FLOW_DIR)/providers/%.mk,%,$(wildcard $(FLOW_DIR)/providers/*.mk))"; exit 1
else
include $(FLOW_DIR)/providers/$(provider).mk
endif

# Shared link→ELF layer — only for providers that build through flow.
ifdef FLOW_BUILT
include $(FLOW_DIR)/build.mk
endif

include $(FLOW_DIR)/sim-run.mk
include $(FLOW_DIR)/targets.mk
