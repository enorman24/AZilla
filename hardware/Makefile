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
verilate_make_jobs ?= 20
veril_output_split ?= 20
veril_output_split_cfuncs ?= 20
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
ifdef preload
	questa_args += +PRELOAD=$(preload)
	vcs_run_args += +PRELOAD=$(preload)
endif
questa_args += -sv_lib $(dpi_library)/ara_dpi -work $(library) -voptargs=+acc
questa_args += -suppress vsim-3009 -suppress vopt-7033

# DPI source files
dpi_src := $(wildcard tb/dpi/*.cc)
dpi     := $(patsubst tb/dpi/%.cc,$(buildpath)/$(dpi_library)/%.o,$(dpi_src))

vlog_args += -suppress vlog-2583 -suppress vlog-13314 -suppress vlog-13233
vlog_args += -work $(library)

# Bender
# Defines
bender_defs += --define NR_LANES=$(nr_lanes) --define VLEN=$(vlen) --define ARIANE_ACCELERATOR_PORT=1
nr_clusters ?= 2
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

# By default tracing enabled
bender_defs += --define PERFETTO_TRACE

bender_defs_veril := $(bender_defs) --define COMMON_CELLS_ASSERTS_OFF

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
.PHONY: apply-patches
apply-patches: patches
	cd deps/tech_cells_generic && git apply ../../patches/0001-tech-cells-generic-sram.patch

# Library
.PHONY: lib
lib: $(buildpath) $(buildpath)/$(library)
$(buildpath)/$(library):
	cd $(buildpath) && $(questa_cmd) vlib $(library) && $(questa_cmd) vmap $(library) $(library)

# Compilation
.PHONY: compile
compile: dpi lib $(buildpath) bender $(buildpath)/compile_$(config).tcl
$(buildpath)/compile_$(config).tcl: $(config_file) Makefile ../Bender.yml $(shell find src -type f) $(shell find ../config -type f) $(shell find include -type f) $(shell find tb -type f) $(shell find deps -type f)
	$(BENDER) script vsim --vlog-arg="$(vlog_args)" $(bender_targs_simc) $(bender_defs) > $(buildpath)/compile_$(config).tcl
	echo "exit" >> $(buildpath)/compile_$(config).tcl
	cd $(buildpath) && $(questa_cmd) vsim -work $(library) -c -do compile_$(config).tcl
	# Rename the file if compilation did not succeed
	if [ `cat $(buildpath)/transcript | grep "\*\* Error" | wc -l` -ne 0 ]; then mv $(buildpath)/compile_$(config).tcl $(buildpath)/compile_$(config).tcl.ERROR; fi

# Simulation
.PHONY: sim
sim: compile
	cd $(buildpath) && \
	$(questa_cmd) vsim $(questa_args) $(library).$(top_level) -do ../scripts/run$(ideal).tcl
	./scripts/return_status.sh $(buildpath)/transcript

.PHONY: simc
simc: compile
	cd $(buildpath) && \
	$(questa_cmd) vsim -c $(questa_args) $(library).$(top_level) -do "run -a"
	./scripts/return_status.sh $(buildpath)/transcript

# VCS
.PHONY: compile_vcs sim_vcs simc_vcs sim_gui_vcs show_vcs
compile_vcs: dpi $(vcs_buildpath) bender $(vcs_binary)

$(vcs_script): $(vcs_buildpath) $(BENDER) $(config_file) Makefile ../Bender.yml $(shell find src -type f) $(shell find ../config -type f) $(shell find include -type f) $(shell find tb -type f) $(shell find deps -type f)
	$(BENDER) script vcs --vlogan-bin=$(vlogan_cmd) --vhdlan-bin=$(vhdlan_cmd) \
	$(foreach arg,$(vlogan_args),--vlog-arg=$(arg)) \
	$(foreach arg,$(vhdlan_args),--vcom-arg=$(arg)) \
	$(bender_targs_vcs) $(bender_defs) > $(vcs_script)
	chmod +x $(vcs_script)

$(vcs_binary): $(vcs_script)
	cd $(vcs_buildpath) && ./$(notdir $(vcs_script))
	cd $(vcs_buildpath) && $(vcs_cmd) -full64 $(vcs_elab_args) \
		-Mdir=$(notdir $(vcs_csrc_dir)) -o $(notdir $(vcs_binary)) $(top_level)

sim_vcs: compile_vcs
	set -o pipefail; cd $(vcs_buildpath) && \
		./$(notdir $(vcs_binary)) -sv_lib $(abspath $(buildpath)/$(dpi_library)/ara_dpi) $(vcs_run_args) 2>&1 | tee transcript
	./scripts/return_status.sh $(vcs_buildpath)/transcript

simc_vcs: sim_vcs

sim_gui_vcs: compile_vcs
	set -o pipefail; cd $(vcs_buildpath) && \
		./$(notdir $(vcs_binary)) -gui -sv_lib $(abspath $(buildpath)/$(dpi_library)/ara_dpi) $(vcs_run_args) 2>&1 | tee transcript
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
.NOTPARALLEL: verilate simv
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
  --hierarchical                                                                \
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
  $(if $(trace),--trace-fst -Wno-INSECURE,)                                     \
  --top-module $(veril_top) &&                                                  \
	cd $(veril_library) && OBJCACHE='' VERILATOR_BIN=$(veril_bin_rel) $(MAKE) -j $(verilate_make_jobs) OPT_FAST='$(veril_opt_fast)' -f V$(veril_top).mk

# Simulation
.PHONY: simv
simv: verilate
	$(veril_library)/V$(veril_top) $(if $(trace),-t,) -l ram,$(app_path)/$(app),elf

.PHONY: riscv_tests_simv
riscv_tests_simv: $(tests)

$(tests): rv%: $(app_path)/rv%
	$(veril_library)/V$(veril_top) $(if $(trace),-t,) -l ram,$<,elf &> $(buildpath)/$@.trace

# Run all RISC-V tests on QuestaSim
.PHONY: riscv_tests_simc
riscv_tests_simc: compile
	@failed_tests=""; \
	GREEN='\033[92m'; RED='\033[91m'; RESET='\033[0m'; \
	echo -e "========================================================================================="; \
	echo -e "Running RISC-V Vector tests on QuestaSim $(nr_lanes) lanes and $(nr_clusters) clusters"; \
	echo -e "========================================================================================="; \
	for test in $(tests); do \
		make simc app=$$test > $(buildpath)/$${test}.log 2>&1; \
		if grep -q "FAILED" $(buildpath)/transcript; then \
			printf "  ✗ %-60s $${RED}FAILED$${RESET}\n" "$$test"; \
			failed_tests="$$failed_tests $$test"; \
		else \
			printf "  ✓ %-60s $${GREEN}PASSED$${RESET}\n" "$$test"; \
		fi; \
		cp $(buildpath)/transcript $(buildpath)/$${test}.transcript; \
	done; \
	if [ -n "$$failed_tests" ]; then \
		echo -e ""; \
		echo -e "==============================================="; \
		echo -e "$${RED}FAILED TESTS:$$failed_tests$${RESET}"; \
		echo -e "==============================================="; \
		exit 1; \
	else \
		echo -e ""; \
		echo -e "==============================================="; \
		echo -e "$${GREEN}ALL TESTS PASSED$${RESET}"; \
		echo -e "==============================================="; \
	fi

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
	$(CXX) -shared -m64 -o $(buildpath)/$(dpi_library)/ara_dpi.so $?

# Clean targets
.PHONY: clean
clean:
	rm -rf $(buildpath)
	rm -f  $(BENDER)
