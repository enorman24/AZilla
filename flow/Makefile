SHELL = /usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════════
#  flow/Makefile — the single, provider-neutral build+sim orchestrator.
#
#  One entry point for every kernel source. An app is named  <provider>:<name>
#  (e.g.  c:fmatmul,  tvm:fdotproduct,  tilelang:dotproduct,  prebuilt:<label>).
#  The orchestrator resolves/builds the ELF for that provider, then runs it
#  through the SHARED run layer (scripts/run-sim.sh) on the SHARED sim binary
#  (resolved by hw-config.mk) — so every provider gets the same run-management
#  UX and reuses the same Verilator/VCS binaries.
#
#  Provider source collections stay in their own dirs (apps/, tvm-apps/,
#  tilelang-apps/); this orchestrator only references them via $(ARA_DIR).
#  See docs/UNIFIED_BUILD_DESIGN.md.
# ════════════════════════════════════════════════════════════════════════════

# NB: use FLOW_DIR (not ROOT_DIR) for all flow-internal includes — apps/common/
# runtime.mk, pulled in by build.mk, reassigns ROOT_DIR to its own dir.
FLOW_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
ARA_DIR  := $(shell git rev-parse --show-toplevel 2>/dev/null || echo $$ARA_DIR)

include $(FLOW_DIR)/config.mk
-include $(FLOW_DIR)/local.mk
include $(FLOW_DIR)/hw-config.mk

app       ?= tvm:fdotproduct
simulator ?= verilator
ifndef RUN_ID
RUN_ID := $(shell date +%Y%m%d_%H%M%S)
endif

# Normalize values that feed string comparisons / paths. config.mk allows inline
# `# comments`, and Make keeps the whitespace before the `#` in the value — strip
# it so e.g. simulator="verilator   " still matches and paths have no embedded spaces.
app       := $(strip $(app))
simulator := $(strip $(simulator))

# ─── Parse  app = <provider>:<name>  ─────────────────────────────────────────
# (e.g. tvm:fdotproduct -> provider=tvm name=fdotproduct slug=tvm/fdotproduct)
provider := $(firstword $(subst :, ,$(app)))
name     := $(patsubst $(provider):%,%,$(app))
APP_SLUG := $(subst :,/,$(app))

# ─── Per-run output tree (flow owns its own build/, never clobbers providers) ─
FLOW_BUILD      := $(FLOW_DIR)/build
APP_DIR         := $(FLOW_BUILD)/$(APP_SLUG)
APP_OBJ_DIR     := $(APP_DIR)/01_cross
APP_BIN_DIR     := $(APP_DIR)/02_link
APP_SIM_DIR     := $(APP_DIR)/03_sim
APP_SIM_RUN_DIR := $(APP_SIM_DIR)/runs/$(RUN_ID)
APP_LOG_DIR     := $(APP_DIR)/logs/$(RUN_ID)

# ─── Tooling (overridable in local.mk) ───────────────────────────────────────
TVM_PYTHON    ?= conda run -n tvm-dev python
SPIKE_DASM    ?= $(ARA_DIR)/install/riscv-isa-sim/bin/spike-dasm
RUN_SIM       := $(FLOW_DIR)/scripts/run-sim.sh
RETURN_STATUS := $(ARA_DIR)/hardware/scripts/return_status.sh
# sim-monitor.sh and artifacts.py (monitor + manifest/report) still live with
# the TVM provider for Phase 1 and are referenced in place; they migrate into
# flow/ in a later phase. run-sim.sh is the one new flow-owned runner.
MONITOR       := $(ARA_DIR)/tvm-apps/scripts/sim-monitor.sh
ARTIFACTS     := $(ARA_DIR)/tvm-apps/pipeline/artifacts.py
# Results tracking (durable, survives distclean — lives outside build/).
RESULTS_DIR   := $(FLOW_DIR)/results
LEDGER        := $(RESULTS_DIR)/ledger.jsonl
NOTES         := $(RESULTS_DIR)/notes.json
META          := $(RESULTS_DIR)/meta.json
RESULTS_MD    := $(FLOW_DIR)/RESULTS.md
# Default assumes the standard sibling layout (<checkout>/../tools/tvm); set the
# real path in local.mk (gitignored) — see local.mk.example.
TVM_HOME         ?= $(ARA_DIR)/../tools/tvm
TVM_LIBRARY_PATH ?= $(TVM_HOME)/build/lib
TVM_PYTHONPATH   ?= $(TVM_HOME)/python
TVM_MANIFEST_ENV := PYTHONPATH=$(ARA_DIR)/tvm-apps:$(TVM_PYTHONPATH):$$PYTHONPATH TVM_HOME=$(TVM_HOME) TVM_LIBRARY_PATH=$(TVM_LIBRARY_PATH)

# The manifest's "sim binary" field tracks whichever simulator actually ran.
SIM_BINARY := $(if $(filter vcs,$(simulator)),$(VCS_BINARY),$(VERIL_BINARY))

VERILATOR_ROOT ?= $(ARA_DIR)/install/verilator
verilate_jobs    ?= 8
verilate_threads ?= 8

# Target ABI (matches the tvm-apps codegen target).
TARGET_TRIPLE := riscv64-unknown-elf
TARGET_MATTR  := +v,+m,+f,+d
TARGET_ABI    := lp64d

# ─── Build provenance (flow-owned builds only) ────────────────────────────────
# Mirrors tvm-apps app-manifest / env-snapshot / audit. Deferred (=) so the
# tvm-provider vars (TVM_LL, TVM_COMPAT, LINK_LD, RISCV_CC, …) resolve at recipe
# time, after build.mk is included.
APP_MANIFEST_CMD = $(TVM_MANIFEST_ENV) $(TVM_PYTHON) $(ARTIFACTS) app-manifest \
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

APP_AUDIT_CMD = $(TVM_MANIFEST_ENV) $(TVM_PYTHON) $(ARTIFACTS) audit \
  --app "$(app)" --app-kind "$(APP_KIND)" --generator "$(GENERATOR_PY)" --main-c "$(BUILD_MAIN_C)" \
  --app-dir "$(APP_DIR)" --ir-dir "$(TVM_IR_DIR)" --tvm-dir "$(TVM_FINAL_DIR)" \
  --obj-dir "$(APP_OBJ_DIR)" --bin-dir "$(APP_BIN_DIR)" --sim-dir "$(APP_SIM_DIR)" \
  --elf "$(ELF)" --llvm-ir "$(TVM_LL)" --compat-llvm-ir "$(TVM_COMPAT)" \
  --linker-script "$(LINK_LD)" --verilator-binary "$(VERIL_BINARY)"

ENV_SNAPSHOT_CMD = $(TVM_MANIFEST_ENV) $(TVM_PYTHON) $(ARTIFACTS) env-snapshot \
  --output "$(APP_BIN_DIR)/env.json" --riscv-cc "$(RISCV_CC)" --git-dir "$(FLOW_DIR)"

.PHONY: sim provider-build verilate compile-vcs view-sim report tvm-ir audit \
        show-config list-binaries list-apps list-configs monitor monitor-latest help \
        clean-sim clean-build distclean check-symbols status

# ════════════════════════════════════════════════════════════════════════════
#  Provider dispatch — set ELF and define how to (re)build it.
#  Each provider only delegates to its existing source-collection Makefile;
#  the orchestrator stays provider-neutral below this block.
# ════════════════════════════════════════════════════════════════════════════
ifeq ($(provider),prebuilt)
  # Run any existing ELF as-is:  make sim app=prebuilt:<label> elf=<path>
  ELF := $(elf)
provider-build:
	@test -n "$(ELF)" || { echo "ERROR: prebuilt requires elf=<path>"; exit 1; }
	@test -f "$(ELF)" || { echo "ERROR: ELF not found: $(ELF)"; exit 1; }

else ifeq ($(provider),c)
  # Hand-written AraXL C kernel: flow compiles the objects from apps/<name>/
  # sources (+ a generated data.S) and links via build.mk — apps/Makefile is no
  # longer invoked (it stays usable standalone). An optional apps/<name>/app.mk
  # can override discovery (set BUILD_MAIN_C / BUILD_EXTRA_INCLUDES / BUILD_KERNEL_DEPS).
  FLOW_BUILT   := 1
  C_SRC_DIR    := $(ARA_DIR)/apps/$(name)
  APP_KIND     := kernel
  GENERATOR_PY := $(wildcard $(C_SRC_DIR)/script/gen_data.py)
  # def_args_<name> available before app.mk so it can derive defines from them.
  include $(ARA_DIR)/apps/common/default_args.mk
  # 'benchmarks' is a wrapper around the other apps (apps/Makefile excludes it), not a kernel.
  ifeq ($(name),benchmarks)
    $(error flow: 'benchmarks' is a wrapper target, not a runnable c kernel)
  endif
  # Clean errors for a mistyped / non-kernel app name (instead of a cryptic clang failure).
  ifeq ($(wildcard $(C_SRC_DIR)),)
    $(error flow: unknown c kernel '$(name)' — no directory $(C_SRC_DIR))
  endif
  -include $(C_SRC_DIR)/app.mk
  BUILD_MAIN_C ?= $(wildcard $(C_SRC_DIR)/main.c)
  ifeq ($(strip $(BUILD_MAIN_C)),)
    $(error flow: $(C_SRC_DIR) has no main.c — set BUILD_MAIN_C in apps/$(name)/app.mk)
  endif
  BUILD_EXTRA_INCLUDES ?= -I$(ARA_DIR)/apps/include -I$(C_SRC_DIR)
  # Per-app compile defines (e.g. fft's -DFFT_SAMPLES). Set in apps/<name>/app.mk.
  BUILD_EXTRA_DEFINES ?=
  # All .c/.S under the app dir except main.c and any in-tree data.S; data.S is
  # (re)generated into the flow tree so apps/ is never written to.
  C_SRCS_FOUND := $(filter-out $(C_SRC_DIR)/main.c,$(shell find $(C_SRC_DIR) \( -name '*.c' -o -name '*.S' \) -not -name data.S 2>/dev/null))
  C_DATA_S     := $(APP_OBJ_DIR)/data.S
  C_DATA_OBJ   := $(APP_OBJ_DIR)/data.S.o
  BUILD_OBJS   := $(foreach s,$(C_SRCS_FOUND),$(APP_OBJ_DIR)/$(subst /,__,$(patsubst $(C_SRC_DIR)/%,%,$(s))).o) $(C_DATA_OBJ)
  ELF          := $(APP_BIN_DIR)/$(name)
provider-build: $(ELF)

else ifeq ($(provider),tvm)
  # TVM kernel/model: IR generation stays in tvm-apps (pipeline/), but the
  # link→ELF is owned by flow/build.mk. The provider only produces the compute
  # object (.ll -> compat-strip -> -x ir compile). FLOW_BUILT pulls in build.mk.
  FLOW_BUILT    := 1
  TVM_SRC_DIR   := $(firstword $(wildcard $(ARA_DIR)/tvm-apps/kernels/$(name) $(ARA_DIR)/tvm-apps/models/$(name)))
  APP_KIND      := $(if $(findstring /models/,$(TVM_SRC_DIR)),model,kernel)
  GENERATOR_PY  := $(TVM_SRC_DIR)/$(name).py
  BUILD_MAIN_C  := $(wildcard $(TVM_SRC_DIR)/$(name)_main.c)
  -include $(TVM_SRC_DIR)/deps.mk             # may set KERNEL_DEPS
  BUILD_KERNEL_DEPS := $(KERNEL_DEPS)
  BUILD_OBJS    := $(APP_OBJ_DIR)/$(name).o
  ELF           := $(APP_BIN_DIR)/$(name)
  TVM_LL        := $(ARA_DIR)/tvm-apps/build/$(name)/00_codegen/final/$(name).ll
  TVM_COMPAT    := $(APP_OBJ_DIR)/$(name)-compat.ll
  TVM_FINAL_DIR := $(ARA_DIR)/tvm-apps/build/$(name)/00_codegen/final
  TVM_IR_DIR    := $(ARA_DIR)/tvm-apps/build/$(name)/00_codegen/ir
# provider-build produces the ELF, then records build provenance (mirrors
# tvm-apps `compile`: build manifest.json + env.json).
provider-build: $(ELF) | $(APP_LOG_DIR)
	@$(APP_MANIFEST_CMD) 2>/dev/null || echo "flow: build manifest skipped (TVM env unavailable)"
	@$(ENV_SNAPSHOT_CMD) 2>/dev/null || true
	@grep -h '^cmd: ' $(APP_LOG_DIR)/compile.log $(APP_LOG_DIR)/link.log 2>/dev/null > $(APP_LOG_DIR)/build.cmd || true

else
  ELF :=
provider-build:
	@echo "ERROR: unknown provider '$(provider)' in app='$(app)'"
	@echo "       expected one of: c | tvm | tilelang | prebuilt"
	@exit 1
endif

# Shared link→ELF layer (only for flow-owned providers). Brings in runtime.mk
# (RISCV_CC/flags/runtime) used by the provider object rules below too.
ifdef FLOW_BUILT
include $(FLOW_DIR)/build.mk
endif

# ─── tvm provider: produce the compute object (.ll -> compat -> -x ir .o) ────
# IR generation is delegated to tvm-apps `tvm-ir`; the LLVM-version compat strip
# (nocreateundeforpoison) and `-x ir` compile are TVM-specific, so they live
# here, not in the provider-neutral build.mk.
ifeq ($(provider),tvm)
# Regenerate IR when the generator .py changes (so an edited kernel is not
# silently linked from stale cached IR); `make tvm-ir` forces it explicitly.
$(TVM_LL): $(GENERATOR_PY)
	$(MAKE) -C $(ARA_DIR)/tvm-apps tvm-ir app=$(name) \
	  nr_lanes=$(nr_lanes) nr_clusters=$(nr_clusters) config=$(config)

tvm-ir:
	$(MAKE) -C $(ARA_DIR)/tvm-apps tvm-ir app=$(name) \
	  nr_lanes=$(nr_lanes) nr_clusters=$(nr_clusters) config=$(config)

$(TVM_COMPAT): $(TVM_LL) | $(APP_OBJ_DIR) $(APP_LOG_DIR)
	@set -o pipefail; { \
	  echo "=== compat-strip $$(date -Iseconds) ==="; \
	  echo "cmd: sed 's/ nocreateundeforpoison//g' $< > $@"; \
	  sed 's/ nocreateundeforpoison//g' $< > $@; \
	} 2>&1 | tee -a $(APP_LOG_DIR)/compile.log; exit $${PIPESTATUS[0]}

$(BUILD_OBJS): $(TVM_COMPAT) | $(APP_OBJ_DIR) $(APP_LOG_DIR)
	@set -o pipefail; { \
	  echo "=== compile TVM object $$(date -Iseconds) ==="; \
	  echo "cmd: $(RISCV_CC) $(RISCV_CCFLAGS) -x ir -c $< -o $@"; \
	  $(RISCV_CC) $(RISCV_CCFLAGS) -x ir -c $< -o $@; \
	} 2>&1 | tee -a $(APP_LOG_DIR)/compile.log; exit $${PIPESTATUS[0]}
endif

# ─── c provider: generate data.S + compile each apps/<name> source to an obj ──
# Mirrors apps/Makefile's discovery + data-gen, but writes data.S and all
# objects into the flow tree (apps/ is never modified). build.mk then links.
ifeq ($(provider),c)
# data.S: run script/gen_data.py with the app's default args, or touch empty.
# Depends on default_args.mk + the config so sweeping sizes/geometry regenerates
# it (it bakes the data sizes in) rather than silently linking stale data.
$(C_DATA_S): $(GENERATOR_PY) $(ARA_DIR)/apps/common/default_args.mk $(ARA_DIR)/config/$(config).mk | $(APP_OBJ_DIR)
	@if [ -n "$(strip $(GENERATOR_PY))" ]; then \
	   echo "gen: cd $(C_SRC_DIR) && $(PYTHON) script/gen_data.py $(subst ",,$(def_args_$(name)))  > $(C_DATA_S)"; \
	   ( cd $(C_SRC_DIR) && $(PYTHON) script/gen_data.py $(subst ",,$(def_args_$(name))) ) > $(C_DATA_S); \
	 else touch $(C_DATA_S); fi

$(C_DATA_OBJ): $(C_DATA_S) | $(APP_OBJ_DIR) $(APP_LOG_DIR)
	@set -o pipefail; { \
	  echo "=== compile data.S $$(date -Iseconds) ==="; \
	  echo "cmd: $(RISCV_CC) $(RISCV_CCFLAGS) -c $< -o $@"; \
	  $(RISCV_CC) $(RISCV_CCFLAGS) -c $< -o $@; \
	} 2>&1 | tee -a $(APP_LOG_DIR)/compile.log; exit $${PIPESTATUS[0]}

# One compile rule per discovered source → collision-safe obj name in flow tree.
define c_compile_src
$(APP_OBJ_DIR)/$(subst /,__,$(patsubst $(C_SRC_DIR)/%,%,$(1))).o: $(1) | $(APP_OBJ_DIR) $(APP_LOG_DIR)
	@set -o pipefail; { \
	  echo "=== compile $(notdir $(1)) $$$$(date -Iseconds) ==="; \
	  echo "cmd: $(RISCV_CC) $(RISCV_CCFLAGS) -I$(dir $(1)) -c $$< -o $$@"; \
	  $(RISCV_CC) $(RISCV_CCFLAGS) -I$(dir $(1)) -c $$< -o $$@; \
	} 2>&1 | tee -a $(APP_LOG_DIR)/compile.log; exit $$$${PIPESTATUS[0]}
endef
$(foreach s,$(C_SRCS_FOUND),$(eval $(call c_compile_src,$(s))))
endif

include $(FLOW_DIR)/sim-run.mk

# ════════════════════════════════════════════════════════════════════════════
#  Shared RTL binary build (delegated to hardware/) — build ONCE per config,
#  reused by every provider.
# ════════════════════════════════════════════════════════════════════════════
verilate:
	$(MAKE) -C $(ARA_DIR)/hardware verilate \
	  buildpath=$(VERIL_BUILD_DIR) nr_lanes=$(nr_lanes) nr_clusters=$(nr_clusters) \
	  mem_latency=$(mem_latency) cva6_latency=$(cva6_latency) ring_latency=$(ring_latency) \
	  config=$(config) veril_cmd=$(VERILATOR_ROOT)/bin/verilator_bin veril_bin_rel=verilator_bin \
	  verilate_make_jobs=$(verilate_jobs) verilate_threads=$(verilate_threads) trace=$(trace_enabled)

compile-vcs:
	$(VCS_ENV) $(MAKE) -C $(ARA_DIR)/hardware compile_vcs \
	  buildpath=$(VCS_BUILD_DIR) nr_lanes=$(nr_lanes) nr_clusters=$(nr_clusters) \
	  mem_latency=$(mem_latency) cva6_latency=$(cva6_latency) ring_latency=$(ring_latency) \
	  config=$(config) gf12_sram=$(gf12_sram)

# ════════════════════════════════════════════════════════════════════════════
#  Inspection / discoverability
# ════════════════════════════════════════════════════════════════════════════
view-sim:
	@run_fsdb="$(APP_SIM_RUN_DIR)/waveform.fsdb"; latest_fsdb="$(APP_SIM_DIR)/latest/waveform.fsdb"; \
	 if [ -f "$$run_fsdb" ]; then fsdb="$$run_fsdb"; elif [ -f "$$latest_fsdb" ]; then fsdb="$$latest_fsdb"; else fsdb=""; fi; \
	 if [ -z "$$fsdb" ]; then echo "view-sim: no FSDB for app=$(app) (VCS runs only). Nothing to view."; exit 0; fi; \
	 echo "view-sim: opening Verdi on $$fsdb"; \
	 $(if $(strip $(LM_LICENSE_FILE)),LM_LICENSE_FILE=$(LM_LICENSE_FILE) ,)$(VERDI) -ssf "$$fsdb"

report:
	@$(TVM_MANIFEST_ENV) $(TVM_PYTHON) $(ARTIFACTS) report --run-dir "$(APP_SIM_RUN_DIR)" --app "$(app)"

monitor: | $(APP_SIM_RUN_DIR)
	@echo "Watching $(APP_SIM_RUN_DIR)/live.log — Ctrl-C to exit"
	@tail --follow=name --retry -n +0 "$(APP_SIM_RUN_DIR)/live.log"

monitor-latest:
	@echo "Watching $(APP_SIM_DIR)/latest/live.log — Ctrl-C to exit"
	@tail --follow=name --retry -n +0 "$(APP_SIM_DIR)/latest/live.log"

show-config:
	@echo "app:              $(app)"
	@echo "  provider:       $(provider)"
	@echo "  name:           $(name)"
	@echo "config:           $(config)"
	@echo "nr_clusters:      $(nr_clusters)"
	@echo "nr_lanes:         $(nr_lanes)"
	@echo "mem/cva6/ring lat: $(mem_latency)/$(cva6_latency)/$(ring_latency)"
	@echo "trace:            $(trace_status)"
	@echo "simulator:        $(simulator)"
	@echo "run id:           $(RUN_ID)"
	@echo "ELF:              $(ELF)"
	@echo "sim binary:       $(SIM_BINARY)"
	@echo "  verilator:      $(VERIL_BINARY)  [$(if $(wildcard $(VERIL_BINARY)),present,MISSING)]"
	@echo "  vcs:            $(VCS_BINARY)  [$(if $(wildcard $(VCS_BINARY)),present,MISSING)]"
	@echo "app dir:          $(APP_DIR)"
	@echo "sim run dir:      $(APP_SIM_RUN_DIR)"

# Which Verilator/VCS binaries exist, across all configs.
list-binaries:
	@echo "=== built RTL-sim binaries under $(ARA_DIR)/hardware ==="
	@for d in $(ARA_DIR)/hardware/build-nc* $(ARA_DIR)/hardware/build-vcs-nc*; do \
	   [ -d "$$d" ] || continue; \
	   if [ -f "$$d/verilator/Vara_tb_verilator" ]; then echo "  [verilator] $$(basename $$d)"; fi; \
	   if [ -f "$$d/vcs/simv" ]; then echo "  [vcs]       $$(basename $$d)"; fi; \
	 done

# Catalog of runnable apps grouped by provider.
list-apps:
	@echo "=== c:        (apps/<name>/main.c) ==="
	@for d in $(ARA_DIR)/apps/*/main.c; do \
	   n=$$(basename $$(dirname $$d)); \
	   [ -f "$$d" ] && [ "$$n" != benchmarks ] && echo "  c:$$n"; done | sort
	@echo "=== tvm:      (tvm-apps/{kernels,models}/<name>/<name>.py) ==="
	@for d in $(ARA_DIR)/tvm-apps/kernels/*/ $(ARA_DIR)/tvm-apps/models/*/; do \
	   n=$$(basename "$$d"); \
	   [ "$$n" = common ] && continue; \
	   [ -f "$$d$$n.py" ] && echo "  tvm:$$n"; done | sort
	@echo "=== tilelang: (tilelang-apps/<name>/) ==="
	@for d in $(ARA_DIR)/tilelang-apps/*/; do [ -d "$$d" ] && echo "  tilelang:$$(basename $$d)"; done | sort 2>/dev/null || true
	@echo "  (also: prebuilt:<label> elf=<path> to run any existing ELF)"

# Available hardware configs (the config=<name> knob).
list-configs:
	@echo "=== hardware configs ($(ARA_DIR)/config/<name>.mk; use config=<name>) ==="
	@for f in $(ARA_DIR)/config/*.mk; do \
	   n=$$(basename "$$f" .mk); \
	   lanes=$$(grep -E '^[[:space:]]*nr_lanes' "$$f" 2>/dev/null | head -1 | grep -oE '[0-9]+' | head -1); \
	   vlen=$$(grep -E '^[[:space:]]*vlen' "$$f" 2>/dev/null | head -1 | grep -oE '[0-9]+' | head -1); \
	   printf "  config=%-10s nr_lanes=%-4s vlen=%s\n" "$$n" "$${lanes:-?}" "$${vlen:-?}"; \
	 done | sort
	@echo "  NOTE: AraXL standard is 'default' (nr_lanes=4). The 2/8/16-lane configs"
	@echo "        are legacy Ara/Ara2 holdovers — rarely used. Scale AraXL with nr_clusters=N."

# Program results matrix -> RESULTS.md. Always re-imports all on-disk runs first
# (merge into the ledger; never loses history) so it is up to date, then renders
# the latest run per (program, simulator, config).
status:
	@$(TVM_MANIFEST_ENV) $(TVM_PYTHON) $(ARTIFACTS) status \
	  --ledger "$(LEDGER)" --ara-dir "$(ARA_DIR)" --notes "$(NOTES)" --meta "$(META)" --out "$(RESULTS_MD)" \
	  --backfill-glob "$(FLOW_BUILD)/*/*/03_sim/runs/*/manifest.json"

# Regenerate pipeline.json + per-app README without a full rebuild (flow-built only).
audit:
	@$(if $(FLOW_BUILT),$(APP_AUDIT_CMD),echo "audit: only meaningful for flow-built providers (tvm); app=$(app)")

# Verify the expected kernel symbol landed in the ELF (flow-built providers).
check-symbols:
	@test -f "$(APP_BIN_DIR)/$(name).syms" || \
	  { echo "ERROR: no symbol table at $(APP_BIN_DIR)/$(name).syms — run 'make sim app=$(app)' first"; exit 1; }
	@echo "=== function symbols containing '$(name)' ==="
	@grep -E ' F ' "$(APP_BIN_DIR)/$(name).syms" | grep "$(name)" || \
	  { echo "WARNING: no function symbol containing '$(name)' in $(name).syms"; exit 1; }

clean-sim:
	rm -rf "$(APP_SIM_DIR)"

# Remove build artifacts for this app (keeps sim runs under 03_sim).
clean-build:
	@if [ -d "$(APP_DIR)" ]; then \
	   find "$(APP_DIR)" -mindepth 1 -maxdepth 1 ! -name 03_sim -exec rm -rf {} +; \
	 fi

# Remove all flow build artifacts and sim runs (keeps the shared lib/ + linker scripts).
distclean:
	@if [ -d "$(FLOW_BUILD)" ]; then \
	   find "$(FLOW_BUILD)" -mindepth 1 -maxdepth 1 ! -name lib -exec rm -rf {} +; \
	 fi

help:
	@echo "flow/ — unified AraXL build+sim orchestrator"
	@echo ""
	@echo "Usage:  make <target> app=<provider>:<name> [VAR=val ...]"
	@echo ""
	@echo "Discover:  make list-apps   (what to build)"
	@echo "           make list-configs (valid config= values)"
	@echo "           make list-binaries (which sim binaries are built)"
	@echo "           make show-config app=<id>  (resolved paths for one app)"
	@echo "           make status      (results matrix: did each program pass?)"
	@echo ""
	@echo "Targets:"
	@echo "  sim            Build (per provider) + run ELF on the RTL sim with full run UX"
	@echo "  verilate       Build the shared Verilator binary for this hardware config"
	@echo "  compile-vcs    Build the shared VCS binary for this hardware config"
	@echo "  view-sim       Open Verdi on the latest FSDB (VCS runs only)"
	@echo "  report         Print sim run summary (RUN_ID=... or latest)"
	@echo "  monitor[-latest] Tail the live monitor for a run"
	@echo "  show-config    Print resolved provider/ELF/binary/paths"
	@echo "  list-apps      Catalog of runnable apps by provider"
	@echo "  list-configs   Available hardware configs (the config= knob)"
	@echo "  list-binaries  Which Verilator/VCS binaries exist (all configs)"
	@echo "  tvm-ir         Force-regenerate TVM IR (tvm: provider)"
	@echo "  audit          Regenerate pipeline.json + README (flow-built)"
	@echo "  check-symbols  Verify the kernel symbol is in the ELF"
	@echo "  status         Program results matrix -> RESULTS.md (imports all runs, always up to date)"
	@echo "  clean-sim      Remove sim runs for this app"
	@echo "  clean-build    Remove build artifacts for this app (keeps sim runs)"
	@echo "  distclean      Remove all flow build artifacts + sim runs (keeps lib/)"
	@echo ""
	@echo "Key variables (set on cmd line or in config.mk):"
	@echo "  app=<provider>:<name>   c: | tvm: | tilelang: | prebuilt:  (e.g. c:fmatmul)"
	@echo "  simulator=verilator|vcs   config=NAME"
	@echo "  nr_clusters=N           AraXL scaling knob (number of Ara2 clusters)"
	@echo "  nr_lanes=N              lanes/cluster — AraXL standard is 4; rarely change"
	@echo "  mem_latency / cva6_latency / ring_latency = cycles (require re-verilate)"
	@echo "  trace=0|1   sim_cycles=N   elf=<path> (prebuilt only)"
