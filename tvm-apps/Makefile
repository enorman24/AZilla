SHELL = /usr/bin/env bash

ROOT_DIR := $(patsubst %/,%, $(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
TVM_APPS_DIR := $(ROOT_DIR)
ARA_DIR := $(shell git rev-parse --show-toplevel 2>/dev/null || echo $$ARA_DIR)
ARTIFACTS_DIR := $(ROOT_DIR)/build
COMMON_DIR := $(ARA_DIR)/apps/common
KERNEL_DIR := $(ROOT_DIR)/kernels
MODEL_DIR := $(ROOT_DIR)/models
LIB_DIR := $(ARTIFACTS_DIR)/lib
ARAXL_LIB := $(LIB_DIR)/libaraxl_kernels.a

include $(ROOT_DIR)/config.mk
-include $(ROOT_DIR)/local.mk
-include $(KERNEL_DIR)/$(app)/deps.mk
-include $(MODEL_DIR)/$(app)/deps.mk

app ?= dotproduct
nr_lanes ?= 4
nr_clusters ?= 2
verilate_jobs    ?= 8
verilate_threads ?= 8
mem_latency  ?= 0
cva6_latency ?= 0
ring_latency ?= 0
ifndef RUN_ID
RUN_ID := $(shell date +%Y%m%d_%H%M%S)
endif
sim_cycles ?=
trace_enabled := $(if $(filter 1 true yes on,$(strip $(trace))),1,)
trace_status := $(if $(trace_enabled),1,0)
SIM_CYCLE_ARG := $(if $(strip $(sim_cycles)),--term-after-cycles=$(sim_cycles),)

APP_DIR         := $(ARTIFACTS_DIR)/$(app)
APP_CODEGEN_DIR := $(APP_DIR)/00_codegen
APP_IR_DIR      := $(APP_CODEGEN_DIR)/ir
APP_TVM_DIR     := $(APP_CODEGEN_DIR)/final
APP_OBJ_DIR     := $(APP_DIR)/01_cross
APP_BIN_DIR     := $(APP_DIR)/02_link
APP_SIM_DIR     := $(APP_DIR)/03_sim
APP_LOG_RUN_DIR := $(APP_DIR)/logs/$(RUN_ID)
APP_SIM_RUN_DIR := $(APP_SIM_DIR)/runs/$(RUN_ID)
APP_MANIFEST := $(APP_DIR)/manifest.json
RAW_DASM := $(APP_SIM_RUN_DIR)/trace_hart_00.dasm
SPIKE_DASM_LOG := $(APP_SIM_RUN_DIR)/trace_hart_00.log

LL_FILE := $(APP_TVM_DIR)/$(app).ll
MAIN_C := $(firstword \
	$(wildcard $(KERNEL_DIR)/$(app)/$(app)_main.c) \
	$(wildcard $(MODEL_DIR)/$(app)/$(app)_main.c))
APP_KIND := $(if $(wildcard $(KERNEL_DIR)/$(app)/$(app).py),kernel,$(if $(wildcard $(MODEL_DIR)/$(app)/$(app).py),model,unknown))
GENERATOR_PY := $(firstword \
	$(wildcard $(KERNEL_DIR)/$(app)/$(app).py) \
	$(wildcard $(MODEL_DIR)/$(app)/$(app).py))
TVM_OBJ := $(APP_OBJ_DIR)/$(app).o
LL_COMPAT := $(APP_OBJ_DIR)/$(app)-compat.ll
MAIN_OBJ  := $(APP_OBJ_DIR)/main.c.o
LINK_LD := $(LIB_DIR)/link-nc$(nr_clusters)-l$(nr_lanes).ld
ELF := $(APP_BIN_DIR)/$(app)
_mem_lat_sfx  := $(if $(filter-out 0,$(mem_latency)),-ml$(mem_latency),)
_cva6_lat_sfx := $(if $(filter-out 0,$(cva6_latency)),-cl$(cva6_latency),)
_ring_lat_sfx := $(if $(filter-out 0,$(ring_latency)),-rl$(ring_latency),)
VERIL_BUILD_DIR := build-nc$(nr_clusters)-l$(nr_lanes)$(_mem_lat_sfx)$(_cva6_lat_sfx)$(_ring_lat_sfx)$(if $(trace_enabled),-trace,)
VERIL_BINARY := $(ARA_DIR)/hardware/$(VERIL_BUILD_DIR)/verilator/Vara_tb_verilator
VCS_BUILD_DIR    := build-vcs-nc$(nr_clusters)-l$(nr_lanes)$(_mem_lat_sfx)$(_cva6_lat_sfx)$(_ring_lat_sfx)
VCS_BINARY       ?= $(ARA_DIR)/hardware/$(VCS_BUILD_DIR)/vcs/simv
VCS_DPI_LIB      ?= $(ARA_DIR)/hardware/$(VCS_BUILD_DIR)/work-dpi/ara_dpi
# EDA tool env. VCS_HOME / LM_LICENSE_FILE are inherited from the shell
# environment (e.g. your site EDA setup script) or set in local.mk. They are
# only injected into the sub-make when actually set, so an unset value never
# clobbers the inherited PATH / license. VERDI defaults to the command name.
VERDI            ?= verdi
VCS_ENV          := $(if $(strip $(VCS_HOME)),VCS_HOME=$(VCS_HOME) PATH=$(VCS_HOME)/bin:$$PATH ,)$(if $(strip $(LM_LICENSE_FILE)),LM_LICENSE_FILE=$(LM_LICENSE_FILE) ,)


KERNEL_DEP_OBJS := $(patsubst %.c, $(LIB_DIR)/%.o, $(notdir $(KERNEL_DEPS)))


RUNTIME_LLVM := \
  $(COMMON_DIR)/crt0-llvm.S.o \
  $(COMMON_DIR)/printf-llvm.c.o \
  $(COMMON_DIR)/string-llvm.c.o \
  $(COMMON_DIR)/serial-llvm.c.o \
  $(COMMON_DIR)/util-llvm.c.o

include $(COMMON_DIR)/runtime.mk
RISCV_CCFLAGS += -I$(COMMON_DIR)
RISCV_LDFLAGS += -nostdlib
RISCV_BUILTINS ?= $(ARA_DIR)/install/riscv-llvm/lib/linux/libclang_rt.builtins-riscv64.a
RISCV_CXXFLAGS += -I$(COMMON_DIR)

TVM_PYTHON ?= conda run -n tvm-dev python
SPIKE_DASM ?= $(ARA_DIR)/install/riscv-isa-sim/bin/spike-dasm
# TVM tree paths — override TVM_HOME in local.mk for your machine.
TVM_HOME         ?= /mnt/ssd/enorman/tools/tvm
TVM_LIBRARY_PATH ?= $(TVM_HOME)/build/lib
TVM_PYTHONPATH   ?= $(TVM_HOME)/python
TVM_ENV          := PYTHONPATH=$(TVM_PYTHONPATH):$$PYTHONPATH TVM_HOME=$(TVM_HOME) TVM_LIBRARY_PATH=$(TVM_LIBRARY_PATH)
TVM_OUTPUT_ENV   := ARAXL_APP_IR_DIR="$(APP_IR_DIR)" ARAXL_APP_TVM_DIR="$(APP_TVM_DIR)"
TVM_MANIFEST_ENV := PYTHONPATH=$(TVM_APPS_DIR):$(TVM_PYTHONPATH):$$PYTHONPATH TVM_HOME=$(TVM_HOME) TVM_LIBRARY_PATH=$(TVM_LIBRARY_PATH)
# Verilator — defaults to the AraXL-bundled install from scripts/get-started.sh.
VERILATOR_ROOT   ?= $(ARA_DIR)/install/verilator
APP_MANIFEST_CMD = $(TVM_MANIFEST_ENV) $(TVM_PYTHON) $(TVM_APPS_DIR)/pipeline/artifacts.py app-manifest --output "$(APP_MANIFEST)" --app "$(app)" --app-kind "$(APP_KIND)" --generator "$(GENERATOR_PY)" --main-c "$(MAIN_C)" $(foreach dep,$(KERNEL_DEPS),--kernel-dep "$(dep)") --target-triple "riscv64-unknown-elf" --target-mattr "+v,+m,+f,+d" --target-abi "lp64d" --config "$(config)" --nr-clusters "$(nr_clusters)" --nr-lanes "$(nr_lanes)" --mem-latency "$(mem_latency)" --cva6-latency "$(cva6_latency)" --ring-latency "$(ring_latency)" --trace "$(trace_status)" --tool "TVM_PYTHON=$(TVM_PYTHON)" --tool "RISCV_CC=$(RISCV_CC)" --tool "RISCV_OBJDUMP=$(RISCV_OBJDUMP)" --tool "RISCV_STRIP=$(RISCV_STRIP)" --tool "VERILATOR_BINARY=$(VERIL_BINARY)" --app-dir "$(APP_DIR)" --ir-dir "$(APP_IR_DIR)" --tvm-dir "$(APP_TVM_DIR)" --obj-dir "$(APP_OBJ_DIR)" --bin-dir "$(APP_BIN_DIR)" --sim-dir "$(APP_SIM_DIR)" --elf "$(ELF)" --llvm-ir "$(LL_FILE)" --compat-llvm-ir "$(LL_COMPAT)" --linker-script "$(LINK_LD)" --verilator-binary "$(VERIL_BINARY)"
APP_AUDIT_CMD = $(TVM_MANIFEST_ENV) $(TVM_PYTHON) $(TVM_APPS_DIR)/pipeline/artifacts.py audit --app "$(app)" --app-kind "$(APP_KIND)" --generator "$(GENERATOR_PY)" --main-c "$(MAIN_C)" --app-dir "$(APP_DIR)" --ir-dir "$(APP_IR_DIR)" --tvm-dir "$(APP_TVM_DIR)" --obj-dir "$(APP_OBJ_DIR)" --bin-dir "$(APP_BIN_DIR)" --sim-dir "$(APP_SIM_DIR)" --elf "$(ELF)" --llvm-ir "$(LL_FILE)" --compat-llvm-ir "$(LL_COMPAT)" --linker-script "$(LINK_LD)" --verilator-binary "$(VERIL_BINARY)"

.PHONY: compile compile-kernel compile-model clean-build clean-sim clean-all-build clean-all-sim distclean linker_script sim verilate compile-vcs view-sim help tvm-ir check-main show-artifacts write-app-manifest audit report check-symbols monitor monitor-latest
.PRECIOUS: $(RUNTIME_LLVM)

# compile the dependencies
define compile_dep
$(LIB_DIR)/$(notdir $(1:.c=.o)): $(1) | $(LIB_DIR) $(APP_LOG_RUN_DIR)
	@set -o pipefail; { \
		echo "=== compile dependency $$(date -Iseconds) ==="; \
		echo "cmd: $(RISCV_CC) $(RISCV_CCFLAGS) -I$(dir $(1)) -c $$< -o $$@"; \
		$(RISCV_CC) $(RISCV_CCFLAGS) -I$(dir $(1)) -c $$< -o $$@; \
	} 2>&1 | tee -a $(APP_LOG_RUN_DIR)/compile.log; exit $$$${PIPESTATUS[0]}
endef

$(foreach dep,$(KERNEL_DEPS),$(eval $(call compile_dep,$(dep))))

$(ARAXL_LIB): $(KERNEL_DEP_OBJS) | $(LIB_DIR) $(APP_LOG_RUN_DIR)
	@set -o pipefail; { \
		echo "=== archive extern kernels $$(date -Iseconds) ==="; \
		echo "cmd: $(RISCV_AR) rcs $@ $^"; \
		$(RISCV_AR) rcs $@ $^; \
	} 2>&1 | tee -a $(APP_LOG_RUN_DIR)/compile.log; exit $${PIPESTATUS[0]}

# compile the app binary (kernel or model)
compile: check-main $(ELF)
	@$(APP_MANIFEST_CMD)
	@$(TVM_MANIFEST_ENV) $(TVM_PYTHON) $(TVM_APPS_DIR)/pipeline/artifacts.py env-snapshot \
		--output "$(APP_BIN_DIR)/env.json" \
		--riscv-cc "$(RISCV_CC)" \
		--git-dir "$(ROOT_DIR)"
	@grep '^cmd: ' $(APP_LOG_RUN_DIR)/compile.log > $(APP_LOG_RUN_DIR)/compile.cmd 2>/dev/null || true
	@grep '^cmd: ' $(APP_LOG_RUN_DIR)/link.log > $(APP_LOG_RUN_DIR)/link.cmd 2>/dev/null || true

# compile the kernel binary
compile-kernel: compile


# compile the model binary
compile-model: compile


help:
	@echo ""
	@echo "Edit config.mk to change configuration"
	@echo ""
	@echo "Available targets:"
	@echo "  compile    - Build the kernel ELF binary"
	@echo "  sim        - Run simulation"
	@echo "  verilate   - Build Verilator simulation binary"
	@echo "  compile-vcs - Build VCS simulation binary"
	@echo "  view-sim   - Open Verdi on the latest VCS waveform (FSDB), or do nothing if none exists"
	@echo "  tvm-ir     - Generate the TVM IRs"
	@echo "  monitor        - Tail live.log for a specific run (uses RUN_ID); run in a second pane"
	@echo "  monitor-latest - Tail live.log for the most recent sim run (sim/latest)"
	@echo "  show-artifacts - Print resolved artifact paths and pipeline stages"
	@echo "  audit          - Regenerate pipeline.json and README.md (no full build)"
	@echo "  report         - Print sim run summary (use RUN_ID=... or latest)"
	@echo "  check-symbols  - Verify expected kernel symbol is present in binary"
	@echo "  clean-build       - Remove build artifacts for app=<name> (keeps sim runs)"
	@echo "  clean-sim         - Remove sim runs for app=<name>"
	@echo "  clean-all-build   - Remove build artifacts for all apps (keeps sim runs)"
	@echo "  clean-all-sim     - Remove sim runs for all apps"
	@echo "  distclean         - Remove all build artifacts and sim runs for all apps"


# verilate the hardware
verilate: | $(APP_LOG_RUN_DIR)
	@set -o pipefail; { \
		echo "=== verilate app=$(app) nr_clusters=$(nr_clusters) nr_lanes=$(nr_lanes) mem_latency=$(mem_latency) cva6_latency=$(cva6_latency) ring_latency=$(ring_latency) trace=$(trace_status) $$(date -Iseconds) ==="; \
		echo "cmd: make -C $(ARA_DIR)/hardware verilate buildpath=$(VERIL_BUILD_DIR) nr_lanes=$(nr_lanes) nr_clusters=$(nr_clusters) mem_latency=$(mem_latency) cva6_latency=$(cva6_latency) ring_latency=$(ring_latency) config=$(config) veril_cmd=$(VERILATOR_ROOT)/bin/verilator_bin veril_bin_rel=verilator_bin verilate_make_jobs=$(verilate_jobs) verilate_threads=$(verilate_threads) trace=$(trace_enabled)"; \
		make -C $(ARA_DIR)/hardware verilate \
			buildpath=$(VERIL_BUILD_DIR) \
			nr_lanes=$(nr_lanes) \
			nr_clusters=$(nr_clusters) \
			mem_latency=$(mem_latency) \
			cva6_latency=$(cva6_latency) \
			ring_latency=$(ring_latency) \
			config=$(config) \
			veril_cmd=$(VERILATOR_ROOT)/bin/verilator_bin \
			veril_bin_rel=verilator_bin \
			verilate_make_jobs=$(verilate_jobs) \
			verilate_threads=$(verilate_threads) \
			trace=$(trace_enabled); \
	} 2>&1 | tee -a $(APP_LOG_RUN_DIR)/verilate.log; exit $${PIPESTATUS[0]}


# compile the VCS hardware binary
compile-vcs: | $(APP_LOG_RUN_DIR)
	@set -o pipefail; { \
		echo "=== compile-vcs nr_clusters=$(nr_clusters) nr_lanes=$(nr_lanes) mem_latency=$(mem_latency) cva6_latency=$(cva6_latency) ring_latency=$(ring_latency) $$(date -Iseconds) ==="; \
		echo "cmd: $(VCS_ENV) make -C $(ARA_DIR)/hardware compile_vcs buildpath=$(VCS_BUILD_DIR) nr_lanes=$(nr_lanes) nr_clusters=$(nr_clusters) mem_latency=$(mem_latency) cva6_latency=$(cva6_latency) ring_latency=$(ring_latency) config=$(config)"; \
		$(VCS_ENV) make -C $(ARA_DIR)/hardware compile_vcs \
			buildpath=$(VCS_BUILD_DIR) \
			nr_lanes=$(nr_lanes) \
			nr_clusters=$(nr_clusters) \
			mem_latency=$(mem_latency) \
			cva6_latency=$(cva6_latency) \
			ring_latency=$(ring_latency) \
			config=$(config); \
	} 2>&1 | tee -a $(APP_LOG_RUN_DIR)/compile-vcs.log; exit $${PIPESTATUS[0]}


# simulator on the hardware
ifeq ($(simulator),verilator)
sim: compile
	@test -f $(VERIL_BINARY) || \
		(echo "ERROR: Verilator binary not found at $(VERIL_BINARY). Run 'make verilate' first."; exit 1)
	@mkdir -p $(APP_SIM_RUN_DIR)/inputs
	@ln -sfn runs/$(RUN_ID) $(APP_SIM_DIR)/latest
	@cp $(ELF)          $(APP_SIM_RUN_DIR)/inputs/ 2>/dev/null || true
	@cp $(LL_FILE)      $(APP_SIM_RUN_DIR)/inputs/ 2>/dev/null || true
	@cp $(LL_COMPAT)    $(APP_SIM_RUN_DIR)/inputs/ 2>/dev/null || true
	@cp $(MAIN_C)       $(APP_SIM_RUN_DIR)/inputs/ 2>/dev/null || true
	@cp $(APP_MANIFEST) $(APP_SIM_RUN_DIR)/inputs/manifest.json 2>/dev/null || true
	@cp $(APP_DIR)/pipeline.json $(APP_SIM_RUN_DIR)/inputs/ 2>/dev/null || true
	@set -o pipefail; \
	 start=$$(date -Iseconds); \
	 cmd="make -C $(ARA_DIR)/hardware simv veril_library=$(dir $(VERIL_BINARY)) app_path=$(APP_BIN_DIR) app=$(app) trace=$(trace_enabled) sim_run_dir=$(APP_SIM_RUN_DIR) veril_run_args='$(SIM_CYCLE_ARG)'"; \
	 monitor_pid=""; \
	 if [ -f "$(TVM_APPS_DIR)/scripts/sim-monitor.sh" ]; then \
		bash "$(TVM_APPS_DIR)/scripts/sim-monitor.sh" "$(APP_SIM_RUN_DIR)" --interval 5 >/dev/null 2>&1 & \
		monitor_pid=$$!; \
	 fi; \
	 { \
		printf "=== sim app=$(app) nr_clusters=$(nr_clusters) nr_lanes=$(nr_lanes) mem_latency=$(mem_latency) cva6_latency=$(cva6_latency) ring_latency=$(ring_latency) trace=$(trace_status) run_id=$(RUN_ID) %s ===\n" "$$start"; \
		printf "cmd: %s\n" "$$cmd"; \
		dasm_tail_pid=""; \
		dasm_filter_pid=""; \
		dasm_fifo=""; \
		if [ -x "$(SPIKE_DASM)" ]; then \
			dasm_fifo="$(APP_SIM_RUN_DIR)/.trace_hart_00.fifo"; \
			rm -f "$$dasm_fifo"; \
			if mkfifo "$$dasm_fifo"; then \
				printf "cmd: tail -n +1 -F $(RAW_DASM) | stdbuf -oL $(SPIKE_DASM) > $(SPIKE_DASM_LOG) &\n"; \
				stdbuf -oL "$(SPIKE_DASM)" < "$$dasm_fifo" > "$(SPIKE_DASM_LOG)" & \
				dasm_filter_pid=$$!; \
				tail -n +1 -F "$(RAW_DASM)" > "$$dasm_fifo" 2>/dev/null & \
				dasm_tail_pid=$$!; \
			else \
				printf "WARNING: could not create DASM live FIFO at %s; skipping live spike-dasm\n" "$$dasm_fifo"; \
			fi; \
		else \
			printf "WARNING: spike-dasm not executable at $(SPIKE_DASM); keeping raw DASM only\n"; \
		fi; \
		make -C $(ARA_DIR)/hardware simv \
			veril_library=$(dir $(VERIL_BINARY)) \
			app_path=$(APP_BIN_DIR) \
			app=$(app) \
			trace=$(trace_enabled) \
			sim_run_dir=$(APP_SIM_RUN_DIR) \
			veril_run_args='$(SIM_CYCLE_ARG)'; \
		sim_rc=$$?; \
		if [ -n "$$dasm_tail_pid" ]; then \
			kill "$$dasm_tail_pid" 2>/dev/null || true; \
			wait "$$dasm_tail_pid" 2>/dev/null || true; \
		fi; \
		if [ -n "$$dasm_filter_pid" ]; then \
			wait "$$dasm_filter_pid" 2>/dev/null || true; \
		fi; \
		if [ -n "$$dasm_fifo" ]; then \
			rm -f "$$dasm_fifo"; \
		fi; \
		if [ -f "$(RAW_DASM)" ]; then \
			if [ -x "$(SPIKE_DASM)" ]; then \
				dasm_tmp="$(SPIKE_DASM_LOG).tmp"; \
				printf "cmd: $(SPIKE_DASM) < $(RAW_DASM) > $(SPIKE_DASM_LOG)\n"; \
				if "$(SPIKE_DASM)" < "$(RAW_DASM)" > "$$dasm_tmp"; then \
					mv "$$dasm_tmp" "$(SPIKE_DASM_LOG)"; \
				else \
					rm -f "$$dasm_tmp"; \
					printf "WARNING: final spike-dasm pass failed for $(RAW_DASM)\n"; \
				fi; \
			fi; \
		else \
			printf "WARNING: raw hart trace not found at $(RAW_DASM)\n"; \
		fi; \
		exit $$sim_rc; \
	 } 2>&1 | tee $(APP_SIM_RUN_DIR)/sim.log; \
	 rc=$${PIPESTATUS[0]}; \
	 if [ -n "$$monitor_pid" ]; then \
		kill "$$monitor_pid" 2>/dev/null || true; \
		wait "$$monitor_pid" 2>/dev/null || true; \
	 fi; \
	 end=$$(date -Iseconds); \
	 $(TVM_MANIFEST_ENV) $(TVM_PYTHON) $(TVM_APPS_DIR)/pipeline/artifacts.py sim-manifest \
		--output "$(APP_SIM_RUN_DIR)/manifest.json" \
		--app "$(app)" \
		--run-id "$(RUN_ID)" \
		--simulator "verilator" \
		--command "$$cmd" \
		--cwd "$(APP_SIM_RUN_DIR)" \
		--elf "$(ELF)" \
		--verilator-binary "$(VERIL_BINARY)" \
		--return-code "$$rc" \
		--start-time "$$start" \
		--end-time "$$end" \
		--config "$(config)" \
		--nr-clusters "$(nr_clusters)" \
		--nr-lanes "$(nr_lanes)" \
		--mem-latency "$(mem_latency)" \
		--cva6-latency "$(cva6_latency)" \
		--ring-latency "$(ring_latency)" \
		--trace "$(trace_status)" \
		--inputs-dir "$(APP_SIM_RUN_DIR)/inputs" \
		--repro-env "TVM_HOME=$(TVM_HOME)" \
		--repro-env "TVM_LIBRARY_PATH=$(TVM_LIBRARY_PATH)" \
		--repro-env "PYTHONPATH=$(TVM_PYTHONPATH):$$PYTHONPATH" \
		--repro-env "nr_clusters=$(nr_clusters)" \
		--repro-env "nr_lanes=$(nr_lanes)"; \
	 exit $$rc
else ifeq ($(simulator), vcs)
sim: compile
	@test -f $(VCS_BINARY) || \
		(echo "ERROR: VCS binary not found at $(VCS_BINARY). Run 'make compile-vcs' first."; exit 1)
	@mkdir -p $(APP_SIM_RUN_DIR)/inputs
	@ln -sfn runs/$(RUN_ID) $(APP_SIM_DIR)/latest
	@cp $(ELF)          $(APP_SIM_RUN_DIR)/inputs/ 2>/dev/null || true
	@cp $(LL_FILE)      $(APP_SIM_RUN_DIR)/inputs/ 2>/dev/null || true
	@cp $(LL_COMPAT)    $(APP_SIM_RUN_DIR)/inputs/ 2>/dev/null || true
	@cp $(MAIN_C)       $(APP_SIM_RUN_DIR)/inputs/ 2>/dev/null || true
	@cp $(APP_MANIFEST) $(APP_SIM_RUN_DIR)/inputs/manifest.json 2>/dev/null || true
	@cp $(APP_DIR)/pipeline.json $(APP_SIM_RUN_DIR)/inputs/ 2>/dev/null || true
	@set -o pipefail; \
	 start=$$(date -Iseconds); \
	 cmd="$(VCS_ENV) make -C $(ARA_DIR)/hardware simv_vcs buildpath=$(VCS_BUILD_DIR) simv_vcs_binary=$(VCS_BINARY) simv_vcs_dpi=$(VCS_DPI_LIB) app_path=$(APP_BIN_DIR) app=$(app) sim_run_dir=$(APP_SIM_RUN_DIR)"; \
	 monitor_pid=""; \
	 if [ -f "$(TVM_APPS_DIR)/scripts/sim-monitor.sh" ]; then \
		bash "$(TVM_APPS_DIR)/scripts/sim-monitor.sh" "$(APP_SIM_RUN_DIR)" --interval 5 >/dev/null 2>&1 & \
		monitor_pid=$$!; \
	 fi; \
	 { \
		printf "=== sim app=$(app) nr_clusters=$(nr_clusters) nr_lanes=$(nr_lanes) mem_latency=$(mem_latency) cva6_latency=$(cva6_latency) ring_latency=$(ring_latency) simulator=vcs run_id=$(RUN_ID) %s ===\n" "$$start"; \
		printf "cmd: %s\n" "$$cmd"; \
		$(VCS_ENV) make -C $(ARA_DIR)/hardware simv_vcs \
			buildpath=$(VCS_BUILD_DIR) \
			simv_vcs_binary=$(VCS_BINARY) \
			simv_vcs_dpi=$(VCS_DPI_LIB) \
			app_path=$(APP_BIN_DIR) \
			app=$(app) \
			sim_run_dir=$(APP_SIM_RUN_DIR); \
		exit $$?; \
	 } 2>&1 | tee $(APP_SIM_RUN_DIR)/sim.log; \
	 rc=$${PIPESTATUS[0]}; \
	 if [ -n "$$monitor_pid" ]; then \
		kill "$$monitor_pid" 2>/dev/null || true; \
		wait "$$monitor_pid" 2>/dev/null || true; \
	 fi; \
	 if [ $$rc -eq 0 ]; then \
		$(ARA_DIR)/hardware/scripts/return_status.sh $(APP_SIM_RUN_DIR)/sim.log; \
		rc=$$?; \
	 fi; \
	 end=$$(date -Iseconds); \
	 $(TVM_MANIFEST_ENV) $(TVM_PYTHON) $(TVM_APPS_DIR)/pipeline/artifacts.py sim-manifest \
		--output "$(APP_SIM_RUN_DIR)/manifest.json" \
		--app "$(app)" \
		--run-id "$(RUN_ID)" \
		--simulator "vcs" \
		--command "$$cmd" \
		--cwd "$(APP_SIM_RUN_DIR)" \
		--elf "$(ELF)" \
		--verilator-binary "$(VCS_BINARY)" \
		--return-code "$$rc" \
		--start-time "$$start" \
		--end-time "$$end" \
		--config "$(config)" \
		--nr-clusters "$(nr_clusters)" \
		--nr-lanes "$(nr_lanes)" \
		--mem-latency "$(mem_latency)" \
		--cva6-latency "$(cva6_latency)" \
		--ring-latency "$(ring_latency)" \
		--trace "$(trace_status)" \
		--inputs-dir "$(APP_SIM_RUN_DIR)/inputs" \
		--repro-env "TVM_HOME=$(TVM_HOME)" \
		--repro-env "TVM_LIBRARY_PATH=$(TVM_LIBRARY_PATH)" \
		--repro-env "PYTHONPATH=$(TVM_PYTHONPATH):$$PYTHONPATH" \
		--repro-env "nr_clusters=$(nr_clusters)" \
		--repro-env "nr_lanes=$(nr_lanes)"; \
	 exit $$rc
endif

# Open Verdi on the FSDB waveform produced by a VCS sim run.
# Prefers a specific run when RUN_ID=<id> is passed; otherwise uses the most
# recent run via the 'latest' symlink. Does nothing (exit 0) if no FSDB exists.
# Note: FSDB waveforms are only produced by VCS sims (make sim simulator=vcs),
# not by Verilator runs.
view-sim:
	@run_fsdb="$(APP_SIM_RUN_DIR)/waveform.fsdb"; \
	latest_fsdb="$(APP_SIM_DIR)/latest/waveform.fsdb"; \
	if [ -f "$$run_fsdb" ]; then fsdb="$$run_fsdb"; \
	elif [ -f "$$latest_fsdb" ]; then fsdb="$$latest_fsdb"; \
	else fsdb=""; fi; \
	if [ -z "$$fsdb" ]; then \
		echo "view-sim: no FSDB waveform found for app=$(app)."; \
		echo "          Run 'make sim app=$(app) simulator=vcs' to generate one. Nothing to view."; \
		exit 0; \
	fi; \
	echo "view-sim: opening Verdi on $$fsdb"; \
	$(if $(strip $(LM_LICENSE_FILE)),LM_LICENSE_FILE=$(LM_LICENSE_FILE) ,)$(VERDI) -ssf "$$fsdb"

tvm-ir:
ifneq ($(wildcard $(KERNEL_DIR)/$(app)/$(app).py),)
	@mkdir -p $(APP_IR_DIR) $(APP_TVM_DIR) $(APP_LOG_RUN_DIR)
	@set -o pipefail; { \
		echo "=== tvm-ir app=$(app) kind=$(APP_KIND) $$(date -Iseconds) ==="; \
		echo "cmd: $(TVM_ENV) $(TVM_OUTPUT_ENV) $(TVM_PYTHON) -m kernels.$(app).$(app)"; \
		$(TVM_ENV) $(TVM_OUTPUT_ENV) $(TVM_PYTHON) -m kernels.$(app).$(app); \
		rc=$$?; \
		if [ $$rc -eq 0 ]; then $(APP_MANIFEST_CMD); fi; \
		exit $$rc; \
	} 2>&1 | tee -a $(APP_LOG_RUN_DIR)/tvm-ir.log; exit $${PIPESTATUS[0]}
else ifneq ($(wildcard $(MODEL_DIR)/$(app)/$(app).py),)
	@mkdir -p $(APP_IR_DIR) $(APP_TVM_DIR) $(APP_LOG_RUN_DIR)
	@set -o pipefail; { \
		echo "=== tvm-ir app=$(app) kind=$(APP_KIND) $$(date -Iseconds) ==="; \
		echo "cmd: $(TVM_ENV) $(TVM_OUTPUT_ENV) $(TVM_PYTHON) -m pipeline.runner --app $(app) --ir-dir $(APP_IR_DIR) --tvm-dir $(APP_TVM_DIR)"; \
		$(TVM_ENV) $(TVM_OUTPUT_ENV) $(TVM_PYTHON) -m pipeline.runner --app $(app) --ir-dir $(APP_IR_DIR) --tvm-dir $(APP_TVM_DIR); \
		rc=$$?; \
		if [ $$rc -eq 0 ]; then $(APP_MANIFEST_CMD); fi; \
		exit $$rc; \
	} 2>&1 | tee -a $(APP_LOG_RUN_DIR)/tvm-ir.log; exit $${PIPESTATUS[0]}
else
	@echo "ERROR: no generator found for app=$(app)"
	@echo "  Expected: $(KERNEL_DIR)/$(app)/$(app).py"
	@echo "         or $(MODEL_DIR)/$(app)/$(app).py"
	@exit 1
endif


$(LINK_LD): $(COMMON_DIR)/script/align_sections.sh $(ARA_DIR)/config/$(config).mk | $(LIB_DIR)
	chmod +x $(COMMON_DIR)/script/align_sections.sh
	rm -f $(LINK_LD) && cp $(COMMON_DIR)/arch.link.ld $@
	$(COMMON_DIR)/script/align_sections.sh $(nr_lanes) $(nr_clusters) $@


$(APP_DIR):
	mkdir -p $@

$(APP_CODEGEN_DIR):
	mkdir -p $@

$(APP_IR_DIR):
	mkdir -p $@

$(APP_TVM_DIR):
	mkdir -p $@

$(APP_OBJ_DIR):
	mkdir -p $@

$(APP_BIN_DIR):
	mkdir -p $@

$(APP_LOG_RUN_DIR):
	mkdir -p $@

$(APP_SIM_RUN_DIR):
	mkdir -p $@


$(LL_FILE):
ifneq ($(wildcard $(KERNEL_DIR)/$(app)/$(app).py),)
	make --no-print-directory tvm-ir app=$(app) RUN_ID=$(RUN_ID)
else ifneq ($(wildcard $(MODEL_DIR)/$(app)/$(app).py),)
	make --no-print-directory tvm-ir app=$(app) RUN_ID=$(RUN_ID)
else
	@echo "ERROR: Missing LL file: $(LL_FILE)"
	@echo "Provide it explicitly with 'LL_FILE=<path>' or add a generator at one of:"
	@echo "  $(KERNEL_DIR)/$(app)/$(app).py"
	@echo "  $(MODEL_DIR)/$(app)/$(app).py"
	@exit 1
endif

# Strip LLVM 21+ attributes unknown to AraXL riscv-llvm 20.x (nocreateundeforpoison)
$(LL_COMPAT): $(LL_FILE) | $(APP_OBJ_DIR) $(APP_LOG_RUN_DIR)
	@set -o pipefail; { \
		echo "=== prepare compatible LLVM IR $$(date -Iseconds) ==="; \
		echo "cmd: sed 's/ nocreateundeforpoison//g' $< > $@"; \
		sed 's/ nocreateundeforpoison//g' $< > $@; \
	} 2>&1 | tee -a $(APP_LOG_RUN_DIR)/compile.log; exit $${PIPESTATUS[0]}

$(TVM_OBJ): $(LL_COMPAT) | $(APP_OBJ_DIR) $(APP_LOG_RUN_DIR)
	@set -o pipefail; { \
		echo "=== compile TVM object $$(date -Iseconds) ==="; \
		echo "cmd: $(RISCV_CC) $(RISCV_CCFLAGS) -x ir -c $< -o $@"; \
		$(RISCV_CC) $(RISCV_CCFLAGS) -x ir -c $< -o $@; \
	} 2>&1 | tee -a $(APP_LOG_RUN_DIR)/compile.log; exit $${PIPESTATUS[0]}


check-main:
	@test -n "$(MAIN_C)" || \
		(echo "ERROR: Missing wrapper C file. Expected one of:"; \
		 echo "  $(KERNEL_DIR)/$(app)/$(app)_main.c"; \
		 echo "  $(MODEL_DIR)/$(app)/$(app)_main.c"; \
		 echo "or provide MAIN_C=<path>"; \
		 exit 1)


$(MAIN_OBJ): $(MAIN_C) | $(APP_OBJ_DIR) $(APP_LOG_RUN_DIR)
	@set -o pipefail; { \
		echo "=== compile wrapper main $$(date -Iseconds) ==="; \
		echo "cmd: $(RISCV_CC) $(RISCV_CCFLAGS) -c $< -o $@"; \
		$(RISCV_CC) $(RISCV_CCFLAGS) -c $< -o $@; \
	} 2>&1 | tee -a $(APP_LOG_RUN_DIR)/compile.log; exit $${PIPESTATUS[0]}


ifneq ($(KERNEL_DEPS),)
ELF_DEPS := $(TVM_OBJ) $(MAIN_OBJ) $(ARAXL_LIB) $(LINK_LD) $(RUNTIME_LLVM)
LIB_FLAGS := -L$(LIB_DIR) -laraxl_kernels
else
ELF_DEPS := $(TVM_OBJ) $(MAIN_OBJ) $(LINK_LD) $(RUNTIME_LLVM)
LIB_FLAGS :=
endif

$(ELF): $(ELF_DEPS) | $(APP_BIN_DIR) $(APP_LOG_RUN_DIR)
	@set -o pipefail -e; { \
		echo "=== link ELF $$(date -Iseconds) ==="; \
		echo "cmd: $(RISCV_CC) $(RISCV_CCFLAGS) $(RISCV_LDFLAGS) $(TVM_OBJ) $(MAIN_OBJ) $(RUNTIME_LLVM) $(LIB_FLAGS) $(RISCV_BUILTINS) -o $@ -T$(LINK_LD) -Wl,-Map=$(APP_BIN_DIR)/$(app).map"; \
		$(RISCV_CC) $(RISCV_CCFLAGS) $(RISCV_LDFLAGS) $(TVM_OBJ) $(MAIN_OBJ) $(RUNTIME_LLVM) $(LIB_FLAGS) $(RISCV_BUILTINS) -o $@ -T$(LINK_LD) -Wl,-Map=$(APP_BIN_DIR)/$(app).map; \
		echo "cmd: $(RISCV_OBJDUMP) $(RISCV_OBJDUMP_FLAGS) -D $@ > $@.dump"; \
		$(RISCV_OBJDUMP) $(RISCV_OBJDUMP_FLAGS) -D $@ > $@.dump; \
		echo "cmd: cp $@ $(APP_BIN_DIR)/$(app).unstripped"; \
		cp $@ $(APP_BIN_DIR)/$(app).unstripped; \
		echo "cmd: $(RISCV_STRIP) $@ -S --strip-unneeded"; \
		$(RISCV_STRIP) $@ -S --strip-unneeded; \
		echo "cmd: $(RISCV_OBJDUMP) --syms $(APP_BIN_DIR)/$(app).unstripped > $(APP_BIN_DIR)/$(app).syms"; \
		$(RISCV_OBJDUMP) --syms $(APP_BIN_DIR)/$(app).unstripped > $(APP_BIN_DIR)/$(app).syms 2>/dev/null || true; \
	} 2>&1 | tee -a $(APP_LOG_RUN_DIR)/link.log; exit $${PIPESTATUS[0]}

$(LIB_DIR):
	mkdir -p $@

write-app-manifest: | $(APP_DIR)
	@$(APP_MANIFEST_CMD)

audit: | $(APP_DIR)
	@$(APP_AUDIT_CMD)

# Print summary for a sim run (defaults to latest; pass RUN_ID=... to target specific run).
report:
	@$(TVM_MANIFEST_ENV) $(TVM_PYTHON) $(TVM_APPS_DIR)/pipeline/artifacts.py report \
		--run-dir "$(APP_SIM_RUN_DIR)" --app "$(app)"

# Fail if no function symbol containing the app name is found in the symbol table.
check-symbols:
	@test -f "$(APP_BIN_DIR)/$(app).syms" || \
		{ echo "ERROR: no symbol table found — run 'make compile app=$(app)' first"; exit 1; }
	@echo "=== function symbols containing '$(app)' ==="
	@grep -E ' F ' "$(APP_BIN_DIR)/$(app).syms" | grep "$(app)" || \
		{ echo "WARNING: no function symbol containing '$(app)' found in $(app).syms"; exit 1; }

show-artifacts:
	@echo "app:             $(app)"
	@echo "kind:            $(APP_KIND)"
	@echo "config:          $(config)"
	@echo "nr_clusters:     $(nr_clusters)"
	@echo "nr_lanes:        $(nr_lanes)"
	@echo "mem_latency:     $(mem_latency)"
	@echo "cva6_latency:    $(cva6_latency)"
	@echo "ring_latency:    $(ring_latency)"
	@echo "simulator:       $(simulator)"
	@echo "sim cycles:      $(sim_cycles)"
	@echo "run id:          $(RUN_ID)"
	@echo "app dir:         $(APP_DIR)"
	@echo "manifest:        $(APP_MANIFEST)"
	@echo "IR dir:          $(APP_IR_DIR)"
	@echo "TVM dir:         $(APP_TVM_DIR)"
	@echo "object dir:      $(APP_OBJ_DIR)"
	@echo "binary dir:      $(APP_BIN_DIR)"
	@echo "log run dir:     $(APP_LOG_RUN_DIR)"
	@echo "sim run dir:     $(APP_SIM_RUN_DIR)"
	@echo "sim latest:      $(APP_SIM_DIR)/latest"
	@echo "raw DASM:        $(RAW_DASM)"
	@echo "spike DASM log:  $(SPIKE_DASM_LOG)"
	@echo "spike-dasm:      $(SPIKE_DASM)"
	@echo "TVM python:      $(TVM_PYTHON)"
	@echo "Verilator binary: $(VERIL_BINARY)"
	@echo "VCS binary:      $(VCS_BINARY)"
	@if [ -d "$(APP_DIR)" ]; then find "$(APP_DIR)" -maxdepth 5 \( -type f -o -type l \) -print | sort; fi
	@if [ -f "$(APP_DIR)/pipeline.json" ]; then \
		echo ""; \
		echo "Pipeline stages:"; \
		$(TVM_PYTHON) -c \
			'import json,sys; d=json.load(open(sys.argv[1])); [print("  [{}] {}".format(s["id"],s["label"])) for s in d["stages"]]' \
			"$(APP_DIR)/pipeline.json"; \
	fi

clean-build:
	@if [ -d "$(APP_DIR)" ]; then \
		find "$(APP_DIR)" -mindepth 1 -maxdepth 1 ! -name 03_sim -exec rm -rf {} +; \
	fi

clean-sim:
	rm -rf "$(APP_SIM_DIR)"

clean-all-build:
	@if [ -d "$(ARTIFACTS_DIR)" ]; then \
		for d in "$(ARTIFACTS_DIR)"/*/; do \
			[ "$$(basename "$$d")" = "lib" ] && continue; \
			[ -d "$$d" ] || continue; \
			find "$$d" -mindepth 1 -maxdepth 1 ! -name 03_sim -exec rm -rf {} +; \
		done; \
	fi

clean-all-sim:
	@if [ -d "$(ARTIFACTS_DIR)" ]; then \
		find "$(ARTIFACTS_DIR)" -mindepth 2 -maxdepth 2 -name 03_sim -type d -exec rm -rf {} +; \
	fi

distclean:
	@if [ -d "$(ARTIFACTS_DIR)" ]; then \
		find "$(ARTIFACTS_DIR)" -mindepth 1 -maxdepth 1 ! -name lib -exec rm -rf {} +; \
	fi

# Tail the live monitor log for a specific run (use in a second pane while make sim runs).
# Pass the same RUN_ID used by the sim invocation, or use monitor-latest.
monitor: | $(APP_SIM_RUN_DIR)
	@echo "Watching $(APP_SIM_RUN_DIR)/live.log — Ctrl-C to exit"
	@tail --follow=name --retry -n +0 "$(APP_SIM_RUN_DIR)/live.log"

# Tail the live monitor log for the most-recent sim run (convenient default).
monitor-latest:
	@echo "Watching $(APP_SIM_DIR)/latest/live.log — Ctrl-C to exit"
	@tail --follow=name --retry -n +0 "$(APP_SIM_DIR)/latest/live.log"
