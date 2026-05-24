SHELL = /usr/bin/env bash

ROOT_DIR := $(patsubst %/,%, $(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
ARA_DIR := $(shell git rev-parse --show-toplevel 2>/dev/null || echo $$ARA_DIR)
ARTIFACTS_DIR := $(ROOT_DIR)/artifacts
COMMON_DIR := $(ARA_DIR)/apps/common
KERNEL_DIR := $(ROOT_DIR)/kernels
MODEL_DIR := $(ROOT_DIR)/models
OUTPUT_DIR := $(ARTIFACTS_DIR)/output
BIN_DIR := $(ARTIFACTS_DIR)/bin
BUILD_DIR := $(ARTIFACTS_DIR)/build
LIB_DIR := $(ARTIFACTS_DIR)/lib
ARAXL_LIB := $(LIB_DIR)/libaraxl_kernels.a

include $(ROOT_DIR)/config.mk
-include $(KERNEL_DIR)/$(app)/deps.mk
-include $(MODEL_DIR)/$(app)/deps.mk

app ?= dotproduct
nr_lanes ?= 4
nr_clusters ?= 2

APP_BUILD_DIR = $(BUILD_DIR)/$(app)

LL_FILE := $(OUTPUT_DIR)/$(app)/$(app).ll
MAIN_C := $(firstword \
	$(wildcard $(KERNEL_DIR)/$(app)/$(app)_main.c) \
	$(wildcard $(MODEL_DIR)/$(app)/$(app)_main.c))
TVM_OBJ := $(APP_BUILD_DIR)/$(app).o
MAIN_OBJ  := $(APP_BUILD_DIR)/main.c.o
LINK_LD := $(BUILD_DIR)/link.ld
ELF := $(BIN_DIR)/$(app)
VERIL_BUILD_DIR := build-nc$(nr_clusters)-l$(nr_lanes)
VERIL_BINARY := $(ARA_DIR)/hardware/$(VERIL_BUILD_DIR)/verilator/Vara_tb_verilator


KERNEL_DEP_OBJS := $(patsubst %.c, $(LIB_DIR)/%.o, $(notdir $(KERNEL_DEPS)))


RUNTIME_LLVM := \
  $(COMMON_DIR)/crt0-llvm.S.o \
  $(COMMON_DIR)/printf-llvm.c.o \
  $(COMMON_DIR)/string-llvm.c.o \
  $(COMMON_DIR)/serial-llvm.c.o \
  $(COMMON_DIR)/util-llvm.c.o

include $(COMMON_DIR)/runtime.mk
RISCV_CCFLAGS += -I$(COMMON_DIR)
RISCV_CXXFLAGS += -I$(COMMON_DIR)


.PHONY: compile compile-kernel compile-model clean linker_script sim verilate help tvm-ir check-main

# compile the dependencies
define compile_dep
$(LIB_DIR)/$(notdir $(1:.c=.o)): $(1) | $(LIB_DIR)
	$(RISCV_CC) $(RISCV_CCFLAGS) -I$(dir $(1)) -c $$< -o $$@
endef

$(foreach dep,$(KERNEL_DEPS),$(eval $(call compile_dep,$(dep))))

$(ARAXL_LIB): $(KERNEL_DEP_OBJS) | $(LIB_DIR)
	$(RISCV_AR) rcs $@ $^

# compile the app binary (kernel or model)
compile: check-main $(ELF)

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
	@echo "  tvm-ir     - Generate the TVM IRs"
	@echo "  clean      - Remove all build artifacts"
	@echo ""
	@echo "Useful overrides:"
	@echo "  app=<name>        - app under kernels/ or models/"
	@echo "  LL_FILE=<path>    - use a pre-generated LLVM IR (.ll)"
	@echo "  MAIN_C=<path>     - use a custom wrapper main.c"


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


$(LL_FILE):
ifneq ($(wildcard $(KERNEL_DIR)/$(app)/$(app).py),)
	python -m kernels.$(app).$(app)
else
	@echo "ERROR: Missing LL file: $(LL_FILE)"
	@echo "Provide it explicitly with 'LL_FILE=<path>' or add kernel generator at $(KERNEL_DIR)/$(app)/$(app).py"
	@exit 1
endif


$(TVM_OBJ): $(LL_FILE) | $(APP_BUILD_DIR)
	$(RISCV_CC) $(RISCV_CCFLAGS) -x ir -c $< -o $@ 


check-main:
	@test -n "$(MAIN_C)" || \
		(echo "ERROR: Missing wrapper C file. Expected one of:"; \
		 echo "  $(KERNEL_DIR)/$(app)/$(app)_main.c"; \
		 echo "  $(MODEL_DIR)/$(app)/$(app)_main.c"; \
		 echo "or provide MAIN_C=<path>"; \
		 exit 1)


$(MAIN_OBJ): $(MAIN_C) | $(APP_BUILD_DIR)
	$(RISCV_CC) $(RISCV_CCFLAGS) -c $< -o $@ 


ifneq ($(KERNEL_DEPS),)
ELF_DEPS := $(TVM_OBJ) $(MAIN_OBJ) $(ARAXL_LIB) $(LINK_LD)
LIB_FLAGS := -L$(LIB_DIR) -laraxl_kernels
else
ELF_DEPS := $(TVM_OBJ) $(MAIN_OBJ) $(LINK_LD)
LIB_FLAGS :=
endif

$(ELF): $(ELF_DEPS) | $(BIN_DIR)
	$(RISCV_CC) $(RISCV_CCFLAGS) $(RISCV_LDFLAGS) $(TVM_OBJ) $(MAIN_OBJ) $(RUNTIME_LLVM) $(LIB_FLAGS) -o $@ -T$(LINK_LD)
	$(RISCV_OBJDUMP) $(RISCV_OBJDUMP_FLAGS) -D $@ > $@.dump
	$(RISCV_STRIP) $@ -S --strip-unneeded

$(LIB_DIR):
	mkdir -p $@

clean:
	rm -rf $(OUTPUT_DIR)
	rm -rf $(BUILD_DIR)
	rm -rf $(BIN_DIR)





