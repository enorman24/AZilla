# ════════════════════════════════════════════════════════════════════════════
#  flow/build.mk — shared link→ELF layer (provider-neutral).
#
#  Consumes a small, clean interface set by the orchestrator/provider:
#     BUILD_OBJS         compute object(s) the provider produced
#     BUILD_MAIN_C       the harness C file with main()
#     BUILD_KERNEL_DEPS  extra C sources to compile + archive (extern kernels)
#     BUILD_EXTRA_INCLUDES  extra -I flags (e.g. tilelang/src)
#     ELF                output ELF path
#     APP_OBJ_DIR / APP_BIN_DIR   per-app object/binary dirs
#  and produces the ELF (+ .dump/.unstripped/.syms) using the SHARED runtime
#  and a per-config linker script. This is the step that was already common
#  between apps/ and tvm-apps/ — now there is one implementation.
#
#  NOTE: this is the retirement target for tvm-apps/Makefile's link half — that
#  Makefile could later `include` this file for its own link to collapse the two.
# ════════════════════════════════════════════════════════════════════════════

# Shared runtime + toolchain flags come from apps/common/runtime.mk. It is
# written for the apps/ CWD, so mirror tvm-apps's overrides:
COMMON_DIR := $(ARA_DIR)/apps/common
include $(COMMON_DIR)/runtime.mk
# runtime.mk's RISCV_FLAGS has -I$(CURDIR)/common (wrong from flow). Point the
# include + each kernel-dep dir at the real locations.
RISCV_CCFLAGS  += -I$(COMMON_DIR) $(BUILD_EXTRA_INCLUDES) $(BUILD_EXTRA_DEFINES)
RISCV_CXXFLAGS += -I$(COMMON_DIR) $(BUILD_EXTRA_INCLUDES) $(BUILD_EXTRA_DEFINES)
# Use absolute paths for the runtime objects (runtime.mk's are relative to apps/)
# and protect them from runtime.mk's `.INTERMEDIATE` (which would delete them).
RUNTIME_LLVM := \
  $(COMMON_DIR)/crt0-llvm.S.o \
  $(COMMON_DIR)/printf-llvm.c.o \
  $(COMMON_DIR)/string-llvm.c.o \
  $(COMMON_DIR)/serial-llvm.c.o \
  $(COMMON_DIR)/util-llvm.c.o
.PRECIOUS: $(RUNTIME_LLVM)
# RISCV_BUILTINS / -nostdlib already come from runtime.mk (the apps builtins fix).

LIB_DIR   := $(FLOW_BUILD)/lib
LINK_LD   := $(LIB_DIR)/link-nc$(nr_clusters)-l$(nr_lanes).ld
MAIN_OBJ  := $(APP_OBJ_DIR)/main.c.o
ARAXL_LIB := $(LIB_DIR)/libaraxl_kernels.a

# Every compile/link step echoes its `cmd:` and tees to a per-run log (mirrors
# tvm-apps's compile.log/link.log), so a failing build leaves a durable trace.
APP_LOG_DIR ?= $(APP_DIR)/logs/$(RUN_ID)

# ─── extern kernel deps → libaraxl_kernels.a ─────────────────────────────────
KERNEL_DEP_OBJS := $(patsubst %.c,$(LIB_DIR)/%.o,$(notdir $(BUILD_KERNEL_DEPS)))
define compile_dep
$(LIB_DIR)/$(notdir $(1:.c=.o)): $(1) | $(LIB_DIR) $(APP_LOG_DIR)
	@set -o pipefail; { \
	  echo "=== compile dep $(notdir $(1)) $$$$(date -Iseconds) ==="; \
	  echo "cmd: $(RISCV_CC) $(RISCV_CCFLAGS) -I$(dir $(1)) -c $$< -o $$@"; \
	  $(RISCV_CC) $(RISCV_CCFLAGS) -I$(dir $(1)) -c $$< -o $$@; \
	} 2>&1 | tee -a $(APP_LOG_DIR)/compile.log; exit $$$${PIPESTATUS[0]}
endef
$(foreach dep,$(BUILD_KERNEL_DEPS),$(eval $(call compile_dep,$(dep))))

$(ARAXL_LIB): $(KERNEL_DEP_OBJS) | $(LIB_DIR) $(APP_LOG_DIR)
	@set -o pipefail; { \
	  echo "cmd: $(RISCV_AR) rcs $@ $^"; \
	  $(RISCV_AR) rcs $@ $^; \
	} 2>&1 | tee -a $(APP_LOG_DIR)/compile.log; exit $${PIPESTATUS[0]}

# ─── main harness ────────────────────────────────────────────────────────────
$(MAIN_OBJ): $(BUILD_MAIN_C) | $(APP_OBJ_DIR) $(APP_LOG_DIR)
	@set -o pipefail; { \
	  echo "=== compile main $$(date -Iseconds) ==="; \
	  echo "cmd: $(RISCV_CC) $(RISCV_CCFLAGS) -c $< -o $@"; \
	  $(RISCV_CC) $(RISCV_CCFLAGS) -c $< -o $@; \
	} 2>&1 | tee -a $(APP_LOG_DIR)/compile.log; exit $${PIPESTATUS[0]}

# ─── per-config linker script (regenerated per hardware geometry) ────────────
$(LINK_LD): $(COMMON_DIR)/script/align_sections.sh $(ARA_DIR)/config/$(config).mk | $(LIB_DIR)
	chmod +x $(COMMON_DIR)/script/align_sections.sh
	rm -f $(LINK_LD) && cp $(COMMON_DIR)/arch.link.ld $@
	$(COMMON_DIR)/script/align_sections.sh $(nr_lanes) $(nr_clusters) $@

# ─── link → ELF (with/without extern-kernel archive) ─────────────────────────
ifneq ($(strip $(BUILD_KERNEL_DEPS)),)
ELF_DEPS  := $(BUILD_OBJS) $(MAIN_OBJ) $(ARAXL_LIB) $(LINK_LD) $(RUNTIME_LLVM)
LIB_FLAGS := -L$(LIB_DIR) -laraxl_kernels
else
ELF_DEPS  := $(BUILD_OBJS) $(MAIN_OBJ) $(LINK_LD) $(RUNTIME_LLVM)
LIB_FLAGS :=
endif

$(ELF): $(ELF_DEPS) | $(APP_BIN_DIR) $(APP_LOG_DIR)
	@set -o pipefail; { \
	  echo "=== link ELF $$(date -Iseconds) ==="; \
	  echo "cmd: $(RISCV_CC) $(RISCV_CCFLAGS) $(RISCV_LDFLAGS) $(BUILD_OBJS) $(MAIN_OBJ) $(RUNTIME_LLVM) $(LIB_FLAGS) $(RISCV_BUILTINS) -o $@ -T$(LINK_LD) -Wl,-Map=$(APP_BIN_DIR)/$(name).map"; \
	  $(RISCV_CC) $(RISCV_CCFLAGS) $(RISCV_LDFLAGS) $(BUILD_OBJS) $(MAIN_OBJ) $(RUNTIME_LLVM) $(LIB_FLAGS) $(RISCV_BUILTINS) -o $@ -T$(LINK_LD) -Wl,-Map=$(APP_BIN_DIR)/$(name).map; \
	  echo "cmd: $(RISCV_OBJDUMP) $(RISCV_OBJDUMP_FLAGS) -D $@ > $@.dump"; \
	  $(RISCV_OBJDUMP) $(RISCV_OBJDUMP_FLAGS) -D $@ > $@.dump; \
	  cp $@ $(APP_BIN_DIR)/$(name).unstripped; \
	  echo "cmd: $(RISCV_STRIP) $@ -S --strip-unneeded"; \
	  $(RISCV_STRIP) $@ -S --strip-unneeded; \
	  $(RISCV_OBJDUMP) --syms $(APP_BIN_DIR)/$(name).unstripped > $(APP_BIN_DIR)/$(name).syms 2>/dev/null || true; \
	} 2>&1 | tee -a $(APP_LOG_DIR)/link.log; exit $${PIPESTATUS[0]}

$(LIB_DIR) $(APP_OBJ_DIR) $(APP_BIN_DIR) $(APP_LOG_DIR):
	mkdir -p $@
