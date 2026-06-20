# Copyright 2021-2025 ETH Zurich and University of Bologna.
# Solderpad Hardware License, Version 0.51, see LICENSE for details.
# SPDX-License-Identifier: SHL-0.51
#
# Author: Matheus Cavalcante <matheusd@iis.ee.ethz.ch>

SHELL = /usr/bin/env bash
ROOT_DIR := $(patsubst %/,%, $(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
ARA_DIR := $(shell git rev-parse --show-toplevel 2>/dev/null || echo $$ARA_DIR)
INSTALL_DIR := $(abspath $(ROOT_DIR)/../install)
VERILATOR_INCLUDE := $(INSTALL_DIR)/verilator/share/verilator/include/vltstd

BENDER         := $(ROOT_DIR)/../hardware/bender
BENDER_VERSION := 0.29.1

# Choose Ara's configuration
ifndef config
	ifdef ARA_CONFIGURATION
		config := $(ARA_CONFIGURATION)
	else
		config := default
	endif
endif

# Include configuration
config_file := $(ROOT_DIR)/../config/$(config).mk
include $(abspath $(ROOT_DIR)/../config/$(config).mk)

# Optional local overrides (gitignored): e.g. GF12_SRAM_DIR for the private GF12 build.
-include $(ROOT_DIR)/local.mk

# Clang flags for Verilator command
ifneq (${CLANG_PATH},)
	CLANG_CXXFLAGS := -CFLAGS "-nostdinc++ -isystem $(CLANG_PATH)/include/c++/v1"
	CLANG_LDFLAGS  := -LDFLAGS "-L $(CLANG_PATH)/lib -Wl,-rpath,$(CLANG_PATH)/lib -lc++ -nostdlib++"
else
	CLANG_CXXFLAGS :=
	CLANG_LDFLAGS  :=
endif

# build path
buildpath      ?= build
resultpath     ?= results
# VCS build path
vcs_buildpath  ?= $(buildpath)/vcs
# VCS generated C sources
vcs_csrc_dir   ?= $(vcs_buildpath)/csrc
# questa library
library        ?= work
# dpi library
dpi_library    ?= work-dpi
# VCS simulation binary
vcs_binary     ?= $(abspath $(vcs_buildpath)/simv)
# VCS compile script
vcs_script     ?= $(vcs_buildpath)/compile_$(config).sh
# VCS waveform output
vcs_fsdb       ?= waveform.fsdb
vcs_fsdb_path  ?= $(abspath $(vcs_buildpath)/$(vcs_fsdb))
# Verdi command
verdi_cmd      ?= verdi
# verilator library
veril_library  ?= $(buildpath)/verilator
# verilator path
veril_path     ?= $(abspath $(INSTALL_DIR)/verilator/bin)
# Use the real binary for the first pass and point recursive wrapper invocations back to it.
veril_cmd      ?= $(abspath $(veril_path)/verilator_bin)
veril_bin_rel  ?= ../../bin/verilator_bin
veril_opt_fast ?= -O0
veril_output_split ?= 1000
veril_output_split_cfuncs ?= 1000
verilate_make_jobs ?= 8
verilate_threads   ?= 8
trace_enabled       := $(if $(filter 1 true yes on,$(strip $(trace))),1,)
veril_hierarchical  ?= $(if $(trace_enabled),0,1)
veril_hierarchical_flag := $(if $(filter 1 true yes on,$(strip $(veril_hierarchical))),--hierarchical,)
veril_trace_flags   := $(if $(trace_enabled),--trace-fst -Wno-INSECURE,)
veril_trace_run_arg := $(if $(trace_enabled),-t,)
veril_run_args      ?=
sim_run_dir         ?= $(CURDIR)
# verilator top-level
veril_top      ?= ara_tb_verilator
# Top level module to compile
top_level      ?= ara_tb
# Questa version
ifeq ($(vcd_dump), 1)
  questa_version ?= 2019.3
else
  questa_version ?= 2021.3
endif
# QuestaSim command
questa_cmd     ?= questa-$(questa_version)
# QuestaSim arguments
questa_args    ?=
# VCS commands
vcs_cmd        ?= vcs
vlogan_cmd     ?= vlogan
vhdlan_cmd     ?= vhdlan
# VCS elaboration/runtime arguments
vcs_elab_args  ?=
vcs_run_args   ?=
vcs_elab_args  += -ignore initializer_driver_checks -kdb -debug_access+all
# VCS compile arguments passed through Bender
vlogan_args    ?=
vhdlan_args    ?=
vlogan_args    += -timescale=1ns/1ps -kdb -debug_access+all
# Ariane's tracer sources include local .svh headers from this directory.
vlogan_args    += +incdir+$(abspath $(ROOT_DIR)/deps/ariane/common/local/util)
# Path to the binaries
app_path       ?= $(abspath $(ROOT_DIR)/../apps/bin)
# Path to ideal dispatcher vtraces
vtrace_path    ?= $(abspath $(ROOT_DIR)/../apps/ideal_dispatcher/vtrace)

ideal          ?=
ifeq ($(ideal_dispatcher), 1)
  vtrace       = $(vtrace_path)/$(app).vtrace
  bender_defs += --define IDEAL_DISPATCHER=1 --define VTRACE="$(vtrace)" --define N_VINSN=$(shell wc -l $(vtrace) | cut -d " " -f 1)
  ideal        = "_ideal"
endif

ifeq ($(vcd_dump), 1)
  vcd_path    ?= ../vcd/$(app).vcd
  bender_defs += --define VCD_DUMP=1 --define VCD_PATH=$(vcd_path)
endif

# Check if the specified QuestaSim version exists when a Questa target is requested.
ifneq ($(strip $(filter lib compile sim simc,$(MAKECMDGOALS))),)
ifeq (, $(shell command -v $(questa_cmd) 2>/dev/null))
  # Spaces are needed for indentation here!
  $(warning "Specified QuestaSim version ($(questa_cmd)) not found in PATH")
  questa_cmd =
endif
endif

questa_args += +UVM_NO_RELNOTES
ifdef app
ifeq ($(ideal_dispatcher), 1)
	preload ?= "$(app_path)/$(app).ideal"
else
	preload ?= "$(app_path)/$(app)"
endif
endif
# DRAM program preload (VCS/Questa): tc_sram.sv loads i_dram from a $readmemh vmem at
# time zero via +DRAM_INIT_FILE. The vmem is generated from the ELF by elf2vmem.py.
# (The Verilator flow loads the ELF via VerilatorMemUtil and is unaffected.)
VMEM_PYTHON ?= python3
ELF2VMEM    := $(abspath $(ROOT_DIR)/scripts/elf2vmem.py)
# nr_clusters default must be declared before dram_bytes_per_word because := expands immediately.
nr_clusters ?= 2
# AxiDataWidth = 32 * NrLanes * NrClusters bits -> bytes_per_word = 4 * NrLanes * NrClusters
dram_bytes_per_word := $(shell expr 4 \* $(nr_lanes) \* $(nr_clusters))
ifdef app
ifeq ($(ideal_dispatcher), 1)
  dram_elf  := $(app_path)/$(app).ideal
else
  dram_elf  := $(app_path)/$(app)
endif
  dram_vmem := $(dram_elf).vmem
endif
ifdef preload
	questa_args  += +DRAM_INIT_FILE=$(dram_vmem)
	vcs_run_args += +DRAM_INIT_FILE=$(dram_vmem)
endif
questa_args += -work $(library) -voptargs=+acc
questa_args += -suppress vsim-3009 -suppress vopt-7033

$(dram_vmem): $(dram_elf) $(ELF2VMEM)
	$(VMEM_PYTHON) $(ELF2VMEM) $< $@ \
	    --dram-base 0x80000000 --dram-length 0x40000000 \
	    --bytes-per-word $(dram_bytes_per_word)

# DPI source files (tb/dpi is empty unless DPI sources are added)
dpi_src := $(wildcard tb/dpi/*.cc)
dpi     := $(patsubst tb/dpi/%.cc,$(buildpath)/$(dpi_library)/%.o,$(dpi_src))

vlog_args += -suppress vlog-2583 -suppress vlog-13314 -suppress vlog-13233
vlog_args += -work $(library)

# Bender
# Defines
bender_defs += --define NR_LANES=$(nr_lanes) --define VLEN=$(vlen) --define ARIANE_ACCELERATOR_PORT=1
ifneq ($(nr_clusters), 0)
	bender_defs += --define USE_CLUSTER=1 --define NR_CLUSTERS=$(nr_clusters)
endif

# Latency arguments for perf simulations
mem_latency ?= 0
ifneq ($(mem_latency), 0)
	bender_defs += --define ADD_MEM_LATENCY=1 --define MEM_LATENCY=$(mem_latency) 
endif

cva6_latency ?= 0
ifneq ($(cva6_latency), 0)
	bender_defs += --define ADD_CVA6_LATENCY=1 --define CVA6_LATENCY=$(cva6_latency) 
endif

ring_latency ?= 0
ifneq ($(ring_latency), 0)
	bender_defs += --define ADD_RING_LATENCY=1 --define RING_LATENCY=$(ring_latency) 
endif

bender_defs_veril := $(bender_defs) --define COMMON_CELLS_ASSERTS_OFF

# VRF bank SRAM backend for VCS/Questa.
#   Public default : behavioral tc_sram (open PULP tech_cells_generic, no IP needed).
#   Private GF12   : pass `gf12_sram=1` with GF12_SRAM_DIR pointing at the private
#                    integration dir (neutral gf12_vrf_bank.sv wrapper + GF12 model).
#                    These sources are never committed to this repo. Set GF12_SRAM_DIR
#                    in hardware/local.mk (gitignored) to avoid passing it each time.
# See hardware/docs/GF12_SRAM.md. Verilator always uses tc_sram (bender_defs_veril).
bender_defs_sim   := $(bender_defs)
GF12_SRAM_DIR     ?=
GF12_SRAM_SRCS    :=
GF12_QUESTA_INJECT := true
GF12_VCS_INJECT    := true
ifeq ($(gf12_sram),1)
  ifeq ($(strip $(GF12_SRAM_DIR)),)
    $(error gf12_sram=1 requires GF12_SRAM_DIR=<private integration dir>; see hardware/docs/GF12_SRAM.md)
  endif
  bender_defs_sim    += --define GF12_SRAM_MACRO=1
  GF12_SRAM_SRCS     := $(wildcard $(GF12_SRAM_DIR)/*.sv)
  vlog_args          += +incdir+$(GF12_SRAM_DIR)
  vlogan_args        += +incdir+$(GF12_SRAM_DIR)
  # Analyze the private wrapper into the same lib, after the bender-listed sources.
  GF12_QUESTA_INJECT := echo 'vlog $(vlog_args) $(GF12_SRAM_SRCS)'
  GF12_VCS_INJECT    := echo 'vlogan -sverilog -full64 $(vlogan_args) $(GF12_SRAM_SRCS)'
endif

# Targets
bender_common_targs := -t rtl -t cv64a6_imafdcv_sv39 -t tech_cells_generic_include_tc_sram -t tech_cells_generic_include_tc_clk
bender_targs_simc     := $(bender_common_targs) -t ara_test -t cva6_test
bender_targs_vcs      := $(bender_common_targs) -t ara_test -t cva6_test
bender_targs_veril    := $(bender_common_targs) -t ara_test -t cva6_test -t verilator
bender_targs_spyglass := $(bender_common_targs) -t spyglass

# Default target
all: compile

# Build path
$(buildpath):
	mkdir -p $(buildpath)

$(vcs_buildpath):
	mkdir -p $(vcs_buildpath)

.PHONY: bender update
# Bender
bender: $(BENDER)
$(BENDER):
	@[ -x $(BENDER) ] && echo "Bender already exists." || \
	curl --proto '=https' --tlsv1.2 https://pulp-platform.github.io/bender/init -sSf | sh	-s -- $(BENDER_VERSION)
	@echo "$$(./bender --version) available."

update: $(BENDER) $(ROOT_DIR)/../Bender.yml
	rm -rf $(ROOT_DIR)/../hardware/deps/*
	$(BENDER) update -f
	$(BENDER) checkout

checkout: $(BENDER)
	$(BENDER) checkout

# Patches
# Apply a Bender dep patch idempotently: skip if already applied, else apply (fail on conflict).
# $(1) = dep dir (relative to hardware/), $(2) = patch filename under hardware/patches/.
define apply_dep_patch
cd $(1) && { git apply --reverse --check $(ROOT_DIR)/patches/$(2) >/dev/null 2>&1 && echo "  [skip] $(2) already applied in $(1)" || { git apply $(ROOT_DIR)/patches/$(2) && echo "  [ok]   applied $(2) to $(1)"; }; }
endef

.PHONY: apply-patches
apply-patches: patches
	@$(call apply_dep_patch,deps/tech_cells_generic,0001-tech-cells-generic-sram.patch)
	@$(call apply_dep_patch,deps/ariane,0002-ariane-araxl.patch)

# Library
.PHONY: lib
lib: $(buildpath) $(buildpath)/$(library)
$(buildpath)/$(library):
	cd $(buildpath) && $(questa_cmd) vlib $(library) && $(questa_cmd) vmap $(library) $(library)

# Compilation
.PHONY: compile
compile: dpi lib $(buildpath) bender $(buildpath)/compile_$(config).tcl
$(buildpath)/compile_$(config).tcl: $(config_file) Makefile ../Bender.yml $(GF12_SRAM_SRCS) $(shell find src -type f) $(shell find ../config -type f) $(shell find include -type f) $(shell find tb -type f) $(shell find deps -type f)
	$(BENDER) script vsim --vlog-arg="$(vlog_args)" $(bender_targs_simc) $(bender_defs_sim) > $(buildpath)/compile_$(config).tcl
	$(GF12_QUESTA_INJECT) >> $(buildpath)/compile_$(config).tcl
	echo "exit" >> $(buildpath)/compile_$(config).tcl
	cd $(buildpath) && $(questa_cmd) vsim -work $(library) -c -do compile_$(config).tcl
	# Rename the file if compilation did not succeed
	if [ `cat $(buildpath)/transcript | grep "\*\* Error" | wc -l` -ne 0 ]; then mv $(buildpath)/compile_$(config).tcl $(buildpath)/compile_$(config).tcl.ERROR; fi

# Simulation
.PHONY: sim
sim: compile $(dram_vmem)
	cd $(buildpath) && \
	$(questa_cmd) vsim $(questa_args) $(library).$(top_level) -do ../scripts/run$(ideal).tcl
	./scripts/return_status.sh $(buildpath)/transcript

.PHONY: simc
simc: compile $(dram_vmem)
	cd $(buildpath) && \
	$(questa_cmd) vsim -c $(questa_args) $(library).$(top_level) -do "run -a"
	./scripts/return_status.sh $(buildpath)/transcript

# VCS
.PHONY: compile_vcs sim_vcs simc_vcs sim_gui_vcs show_vcs
compile_vcs: dpi $(vcs_buildpath) bender $(vcs_binary)

$(vcs_script): $(vcs_buildpath) $(BENDER) $(config_file) Makefile ../Bender.yml $(GF12_SRAM_SRCS) $(shell find src -type f) $(shell find ../config -type f) $(shell find include -type f) $(shell find tb -type f) $(shell find deps -type f)
	$(BENDER) script vcs --vlogan-bin=$(vlogan_cmd) --vhdlan-bin=$(vhdlan_cmd) \
	$(foreach arg,$(vlogan_args),--vlog-arg=$(arg)) \
	$(foreach arg,$(vhdlan_args),--vcom-arg=$(arg)) \
	$(bender_targs_vcs) $(bender_defs_sim) > $(vcs_script)
	$(GF12_VCS_INJECT) >> $(vcs_script)
	chmod +x $(vcs_script)

$(vcs_binary): $(vcs_script)
	cd $(vcs_buildpath) && ./$(notdir $(vcs_script))
	cd $(vcs_buildpath) && $(vcs_cmd) -full64 $(vcs_elab_args) \
		-Mdir=$(notdir $(vcs_csrc_dir)) -o $(notdir $(vcs_binary)) $(top_level)

sim_vcs: compile_vcs $(dram_vmem)
	set -o pipefail; cd $(vcs_buildpath) && \
		./$(notdir $(vcs_binary)) $(vcs_run_args) 2>&1 | tee transcript
	./scripts/return_status.sh $(vcs_buildpath)/transcript

simc_vcs: sim_vcs

sim_gui_vcs: compile_vcs $(dram_vmem)
	set -o pipefail; cd $(vcs_buildpath) && \
		./$(notdir $(vcs_binary)) -gui $(vcs_run_args) 2>&1 | tee transcript
	./scripts/return_status.sh $(vcs_buildpath)/transcript

show_vcs:
	@test -f $(vcs_fsdb_path) || { echo "Missing FSDB: $(vcs_fsdb_path). Run 'make sim_vcs' first."; exit 1; }
	$(verdi_cmd) -ssf $(vcs_fsdb_path)

# RISC-V Tests simulation
APPS_DIR := $(abspath $(ROOT_DIR)/../apps)
TESTS_DIR := $(APPS_DIR)/rvv-tests
include $(TESTS_DIR)/Makefrag
ARA_BINARIES := $(addprefix rvv-tests-ara-, $(ara_tests))

tests := $(ARA_BINARIES)

# Verilator
.PHONY: verilate
verilate: $(buildpath) bender $(veril_library)/V$(veril_top)

$(veril_library)/V$(veril_top): $(config_file) Makefile ../Bender.yml $(shell find src -type f) $(shell find ../config -type f) $(shell find include -type f) $(shell find tb -type f) $(shell find deps -type f)
	rm -rf $(veril_library); mkdir -p $(veril_library)
	$(BENDER) script verilator $(bender_targs_veril) $(bender_defs_veril) > $(veril_library)/bender_script_$(config)
# Verilate the design
	VERILATOR_BIN=$(veril_bin_rel) $(veril_cmd) -f $(veril_library)/bender_script_$(config) \
  -O3                                                                           \
  -Wno-fatal                                                                    \
  -Wno-PINCONNECTEMPTY                                                          \
  -Wno-BLKANDNBLK                                                               \
  -Wno-CASEINCOMPLETE                                                           \
  -Wno-CMPCONST                                                                 \
  -Wno-LATCH                                                                    \
  -Wno-LITENDIAN                                                                \
  -Wno-UNOPTFLAT                                                                \
  -Wno-UNPACKED                                                                 \
  -Wno-UNSIGNED                                                                 \
  -Wno-WIDTH                                                                    \
  -Wno-WIDTHCONCAT                                                              \
  -Wno-ENUMVALUE                                                                \
  -Wno-COMBDLY                                                                  \
  --output-split $(veril_output_split)                                          \
  --output-split-cfuncs $(veril_output_split_cfuncs)                            \
  -fno-dfg                                                                      \
  --threads $(verilate_threads)                                                 \
  $(veril_hierarchical_flag)                                                    \
  tb/verilator/waiver.vlt                                                       \
  --Mdir $(veril_library)                                                       \
  -Itb/dpi                                                                      \
  --compiler clang                                                              \
  -CFLAGS "-DTOPLEVEL_NAME=$(veril_top)"                                        \
  -CFLAGS "-DNR_LANES=$(nr_lanes)"                                              \
  -CFLAGS "-DNR_CLUSTERS=$(nr_clusters)"                                        \
  -CFLAGS -I$(ROOT_DIR)/tb/verilator/lowrisc_dv_verilator_memutil_dpi/cpp       \
  -CFLAGS -I$(ROOT_DIR)/tb/verilator/lowrisc_dv_verilator_memutil_verilator/cpp \
  -CFLAGS -I$(ROOT_DIR)/tb/verilator/lowrisc_dv_verilator_simutil_verilator/cpp \
  $(CLANG_CXXFLAGS)                                                             \
  -LDFLAGS "-lelf"                                                              \
  $(CLANG_LDFLAGS)                                                              \
  --exe                                                                         \
  $(ROOT_DIR)/tb/verilator/lowrisc_dv_verilator_memutil_dpi/cpp/*.cc            \
  $(ROOT_DIR)/tb/verilator/lowrisc_dv_verilator_memutil_verilator/cpp/*.cc      \
  $(ROOT_DIR)/tb/verilator/lowrisc_dv_verilator_simutil_verilator/cpp/*.cc      \
  $(ROOT_DIR)/tb/verilator/ara_tb.cpp                                           \
  --cc                                                                          \
  $(veril_trace_flags)                                                          \
  --top-module $(veril_top) &&                                                  \
	cd $(veril_library) && OBJCACHE='' VERILATOR_BIN=$(veril_bin_rel) $(MAKE) -j $(verilate_make_jobs) OPT_FAST='$(veril_opt_fast)' -f V$(veril_top).mk
	test -x $@

# Simulation
.PHONY: simv
simv:
	mkdir -p $(sim_run_dir)
	cd $(sim_run_dir) && $(abspath $(veril_library)/V$(veril_top)) $(veril_trace_run_arg) $(veril_run_args) -l ram,$(abspath $(app_path))/$(app),elf

simv_vcs_binary ?= $(vcs_binary)
.PHONY: simv_vcs
simv_vcs: $(dram_vmem)
	mkdir -p $(sim_run_dir)
	cd $(sim_run_dir) && \
	$(simv_vcs_binary) \
		$(vcs_run_args)

.PHONY: riscv_tests_simv
riscv_tests_simv: $(tests)

$(tests): rv%: $(app_path)/rv%
	$(veril_library)/V$(veril_top) $(veril_trace_run_arg) -l ram,$<,elf &> $(buildpath)/$@.trace

# Lint
.PHONY: lint spyglass/tmp/files

SNPS_SG ?= spyglass-2022.06
lint: spyglass/tmp/files spyglass/sdc/func.sdc spyglass/scripts/run_lint.tcl
	cd spyglass; $(SNPS_SG) sg_shell -tcl scripts/run_lint.tcl

spyglass/tmp/files: $(bender)
	mkdir -p spyglass/tmp
	$(BENDER) script verilator $(bender_targs_spyglass) $(bender_defs) --define SPYGLASS > spyglass/tmp/files

# DPIs
.PHONY: dpi
dpi: $(buildpath)/$(dpi_library)/ara_dpi.so

$(buildpath)/$(dpi_library)/%.o: tb/dpi/%.cc
	mkdir -p $(buildpath)/$(dpi_library)
	$(CXX) -shared -fPIC -std=c++11 -Bsymbolic -c $< -I$(VERILATOR_INCLUDE) -I$(INSTALL_DIR)/riscv-isa-sim/include -o $@

$(buildpath)/$(dpi_library)/ara_dpi.so: $(dpi)
	mkdir -p $(buildpath)/$(dpi_library)
	@if [ -n "$(strip $(dpi))" ]; then \
		$(CXX) -shared -m64 -o $(buildpath)/$(dpi_library)/ara_dpi.so $?; \
	else \
		echo "No DPI sources (ELF loader replaced by elf2vmem/\$$readmemh); creating empty stub"; \
		: > $(buildpath)/$(dpi_library)/ara_dpi.so; \
	fi

# Clean targets
.PHONY: clean
clean:
	rm -rf $(buildpath)
	rm -f  $(BENDER)
