SHELL = /usr/bin/env bash

ROOT_DIR := $(patsubst %/,%, $(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
ARA_DIR := $(shell git rev-parse --show-toplevel 2>/dev/null || echo $$ARA_DIR)
ARTIFACTS_DIR := $(ROOT_DIR)/artifacts
COMMON_DIR := $(ARA_DIR)/apps/common
KERNEL_DIR := $(ROOT_DIR)/kernels
OUTPUT_DIR := $(ARTIFACTS_DIR)/output
BIN_DIR := $(ARTIFACTS_DIR)/bin
BUILD_DIR := $(ARTIFACTS_DIR)/build

include $(ROOT_DIR)/config.mk

app ?= dotproduct
nr_lanes ?= 4
nr_clusters ?= 2

APP_BUILD_DIR = $(BUILD_DIR)/$(app)

LL_FILE := $(OUTPUT_DIR)/$(app)/$(app).ll
MAIN_C := $(KERNEL_DIR)/$(app)/$(app)_main.c
TVM_OBJ := $(APP_BUILD_DIR)/$(app).o
MAIN_OBJ  := $(APP_BUILD_DIR)/main.c.o
LINK_LD := $(BUILD_DIR)/link.ld
ELF := $(BIN_DIR)/$(app)
VERIL_BUILD_DIR := build-nc$(nr_clusters)-l$(nr_lanes)
VERIL_BINARY := $(ARA_DIR)/hardware/$(VERIL_BUILD_DIR)/verilator/Vara_tb_verilator


RUNTIME_LLVM := \
  $(COMMON_DIR)/crt0-llvm.S.o \
  $(COMMON_DIR)/printf-llvm.c.o \
  $(COMMON_DIR)/string-llvm.c.o \
  $(COMMON_DIR)/serial-llvm.c.o \
  $(COMMON_DIR)/util-llvm.c.o

include $(COMMON_DIR)/runtime.mk
RISCV_CCFLAGS += -I$(COMMON_DIR)
RISCV_CXXFLAGS += -I$(COMMON_DIR)


.PHONY: compile clean linker_script sim verilate help tvm-ir

# compile the kernel binary
compile: $(ELF)


help:
	@echo ""
	@echo "Edit config.mk to change configuration"
	@echo ""
	@echo "Available targets:"
	@echo "  compile    - Build the kernel ELF binary"
	@echo "  sim        - Run simulation"
	@echo "  verilate   - Build Verilator simulation binary"
	@echo "  tvm-ir     - Generate the TVM IRs"
	@echo "  clean      - Remove all build artifacts"


# verilate the hardware
verilate:
	$(MAKE) -C $(ARA_DIR)/hardware verilate \
		buildpath=$(VERIL_BUILD_DIR) \
		nr_lanes=$(nr_lanes) \
		nr_clusters=$(nr_clusters) \
		config=$(config) 


# simulator on the hardware
ifeq ($(simulator),verilator)
sim: compile
	@test -f $(VERIL_BINARY) || \
		(echo "ERROR: Verilator binary not found at $(VERIL_BINARY). Run 'make verilate' first."; exit 1)
	$(MAKE) -C $(ARA_DIR)/hardware simv \
		veril_library=$(dir $(VERIL_BINARY)) \
		app_path=$(BIN_DIR) \
		app=$(app)
else ifeq ($(simulator), vcs)
sim: compile
	@echo "VCS simulator not yet configured"
endif


tvm-ir:
	python -m kernels.$(app).$(app)


$(LINK_LD): $(COMMON_DIR)/script/align_sections.sh $(ARA_DIR)/config/$(config).mk | $(BUILD_DIR)
	chmod +x $(COMMON_DIR)/script/align_sections.sh
	rm -f $(BUILD_DIR)/link.ld && cp $(COMMON_DIR)/arch.link.ld $@
	$(COMMON_DIR)/script/align_sections.sh $(nr_lanes) $(nr_clusters) $@


$(APP_BUILD_DIR):
	mkdir -p $@

$(BIN_DIR):
	mkdir -p $@


# set python location?
$(LL_FILE):
	python -m kernels.$(app).$(app)


$(TVM_OBJ): $(LL_FILE) | $(APP_BUILD_DIR)
	$(RISCV_CC) $(RISCV_CCFLAGS) -x ir -c $< -o $@ 


$(MAIN_OBJ): $(MAIN_C) | $(APP_BUILD_DIR)
	$(RISCV_CC) $(RISCV_CCFLAGS) -c $< -o $@ 


$(ELF): $(TVM_OBJ) $(MAIN_OBJ) $(LINK_LD) | $(BIN_DIR)
	$(RISCV_CC) $(RISCV_CCFLAGS) $(RISCV_LDFLAGS) $(TVM_OBJ) $(MAIN_OBJ) $(RUNTIME_LLVM) -o $@ -T$(LINK_LD)
	$(RISCV_OBJDUMP) $(RISCV_OBJDUMP_FLAGS) -D $@ > $@.dump
	$(RISCV_STRIP) $@ -S --strip-unneeded


clean:
	rm -rf $(ARTIFACTS_DIR)





