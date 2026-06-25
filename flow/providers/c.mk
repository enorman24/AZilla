# providers/c.mk — hand-written AraXL C kernel in apps/<name>/.
#   verilator / vcs : flow compiles apps/<name> sources (+ a generated data.S)
#                     and links via build.mk; apps/Makefile is left untouched.
#   spike           : the RTL ELF can't run on Spike (HTIF vs RTL-eoc exit, and
#                     GCC↔LLVM objects don't mix), so delegate a GCC+HTIF .spike
#                     build to apps/Makefile and stage the result here.

C_SRC_DIR    := $(ARA_DIR)/apps/$(name)
APP_KIND     := kernel
GENERATOR_PY := $(wildcard $(C_SRC_DIR)/script/gen_data.py)
include $(ARA_DIR)/apps/common/default_args.mk   # def_args_<name>, used by data.S gen

ifeq ($(name),benchmarks)
  $(error flow: 'benchmarks' is a wrapper target, not a runnable c kernel)
endif
ifeq ($(wildcard $(C_SRC_DIR)),)
  $(error flow: unknown c kernel '$(name)' — no directory $(C_SRC_DIR))
endif

ifeq ($(simulator),spike)
  # No FLOW_BUILT → build.mk's LLVM link is skipped. apps/Makefile only has a
  # .spike rule for app dirs with a literal main.c, so guard for a clean error
  # (goal-scoped, so show-config/list/help still work without one).
  ifneq ($(filter sim provider-build,$(_GOALS)),)
  ifeq ($(strip $(wildcard $(C_SRC_DIR)/main.c)),)
    $(error flow: simulator=spike needs apps/$(name)/main.c)
  endif
  endif
  ELF := $(APP_BIN_DIR)/$(name).spike
provider-build:
	@echo ">> flow: building Spike ELF for c:$(name) (GCC+HTIF, via apps/Makefile)"
	@# apps/Makefile's %.o.spike rules ignore config, so wipe this app's objects to
	@# force a rebuild for the requested geometry (else a stale one gets relinked).
	@find $(C_SRC_DIR) -name '*.o.spike' -delete 2>/dev/null || true
	$(MAKE) -C $(ARA_DIR)/apps bin/$(name).spike config=$(config) nr_lanes=$(nr_lanes) nr_clusters=$(nr_clusters)
	@mkdir -p $(APP_BIN_DIR)
	cp $(ARA_DIR)/apps/bin/$(name).spike $(ELF)
else
  # LLVM → RTL path. Optional apps/<name>/app.mk overrides discovery
  # (BUILD_MAIN_C / BUILD_EXTRA_INCLUDES / BUILD_EXTRA_DEFINES / BUILD_KERNEL_DEPS).
  FLOW_BUILT   := 1
  -include $(C_SRC_DIR)/app.mk
  BUILD_MAIN_C ?= $(wildcard $(C_SRC_DIR)/main.c)
  ifeq ($(strip $(BUILD_MAIN_C)),)
    $(error flow: $(C_SRC_DIR) has no main.c — set BUILD_MAIN_C in apps/$(name)/app.mk)
  endif
  BUILD_EXTRA_INCLUDES ?= -I$(ARA_DIR)/apps/include -I$(C_SRC_DIR)
  BUILD_EXTRA_DEFINES  ?=
  C_SRCS_FOUND := $(filter-out $(C_SRC_DIR)/main.c,$(shell find $(C_SRC_DIR) \( -name '*.c' -o -name '*.S' \) -not -name data.S 2>/dev/null))
  C_DATA_S     := $(APP_OBJ_DIR)/data.S
  C_DATA_OBJ   := $(APP_OBJ_DIR)/data.S.o
  BUILD_OBJS   := $(foreach s,$(C_SRCS_FOUND),$(APP_OBJ_DIR)/$(subst /,__,$(patsubst $(C_SRC_DIR)/%,%,$(s))).o) $(C_DATA_OBJ)
  ELF          := $(APP_BIN_DIR)/$(name)
provider-build: $(ELF)
endif

# Compile rules (LLVM/RTL path only; recipes use build.mk's RISCV_CC, resolved at
# build time). data.S is regenerated into the flow tree — apps/ is never written —
# keyed on config so a geometry sweep refreshes it.
ifdef FLOW_BUILT
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

# One rule per discovered source → collision-safe object name in the flow tree.
# RISCV_CC/RISCV_CCFLAGS are $$-escaped so they defer to recipe-execution time:
# this define is $(eval)'d when c.mk is included, which is BEFORE build.mk defines
# them. Everything else ($(1), $(dir), $(APP_OBJ_DIR)…) must resolve at eval time.
define c_compile_src
$(APP_OBJ_DIR)/$(subst /,__,$(patsubst $(C_SRC_DIR)/%,%,$(1))).o: $(1) | $(APP_OBJ_DIR) $(APP_LOG_DIR)
	@set -o pipefail; { \
	  echo "=== compile $(notdir $(1)) $$$$(date -Iseconds) ==="; \
	  echo "cmd: $$(RISCV_CC) $$(RISCV_CCFLAGS) -I$(dir $(1)) -c $$< -o $$@"; \
	  $$(RISCV_CC) $$(RISCV_CCFLAGS) -I$(dir $(1)) -c $$< -o $$@; \
	} 2>&1 | tee -a $(APP_LOG_DIR)/compile.log; exit $$$${PIPESTATUS[0]}
endef
$(foreach s,$(C_SRCS_FOUND),$(eval $(call c_compile_src,$(s))))
endif
