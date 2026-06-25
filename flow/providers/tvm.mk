# providers/tvm.mk — TVM kernel/model. IR is generated in tvm-apps/ (pipeline/);
# flow assembles TVM's emitted object and links via build.mk. Needs the TVM env
# (TVM_PYTHON) for IR generation.

FLOW_BUILT    := 1
TVM_SRC_DIR   := $(firstword $(wildcard $(ARA_DIR)/tvm-apps/kernels/$(name) $(ARA_DIR)/tvm-apps/models/$(name)))
APP_KIND      := $(if $(findstring /models/,$(TVM_SRC_DIR)),model,kernel)
GENERATOR_PY  := $(TVM_SRC_DIR)/$(name).py
BUILD_MAIN_C  := $(wildcard $(TVM_SRC_DIR)/$(name)_main.c)
-include $(TVM_SRC_DIR)/deps.mk          # may set KERNEL_DEPS
BUILD_KERNEL_DEPS := $(KERNEL_DEPS)
BUILD_OBJS    := $(APP_OBJ_DIR)/$(name).o
ELF           := $(APP_BIN_DIR)/$(name)

# TVM's LLVM is 22.x, AraXL's clang is 20.x. Recompiling TVM's .ll through clang-20
# MISCOMPILES it (proven on qwen3_toy), so by default assemble TVM's own .s (bit-exact).
#   tvm_codegen=asm  assemble TVM's .s         (default; correct)
#   tvm_codegen=ir   recompile .ll via clang-20 (legacy; miscompiles — A/B debug only)
tvm_codegen   ?= asm
TVM_LL        := $(ARA_DIR)/tvm-apps/build/$(name)/00_codegen/final/$(name).ll
TVM_S         := $(ARA_DIR)/tvm-apps/build/$(name)/00_codegen/final/$(name).s
TVM_COMPAT    := $(APP_OBJ_DIR)/$(name)-compat.ll
TVM_FINAL_DIR := $(ARA_DIR)/tvm-apps/build/$(name)/00_codegen/final
TVM_IR_DIR    := $(ARA_DIR)/tvm-apps/build/$(name)/00_codegen/ir

# provider-build = ELF + surfaced IRs + build provenance (manifest/pipeline/env).
provider-build: $(ELF) | $(APP_LOG_DIR)
	@# Surface the TVM IRs (stage TIR/Relax + final .ll/.s) into the flow tree, so a
	@# flow-driven build is self-describing. Codegen writes them under tvm-apps/build/.
	@mkdir -p $(APP_DIR)/00_codegen
	@cp -rf $(ARA_DIR)/tvm-apps/build/$(name)/00_codegen/. $(APP_DIR)/00_codegen/ 2>/dev/null || true
	@$(APP_MANIFEST_CMD) 2>/dev/null || echo "flow: build manifest skipped (artifacts.py unavailable)"
	@$(ENV_SNAPSHOT_CMD) 2>/dev/null || true
	@grep -h '^cmd: ' $(APP_LOG_DIR)/compile.log $(APP_LOG_DIR)/link.log 2>/dev/null > $(APP_LOG_DIR)/build.cmd || true

# IR generation is delegated to tvm-apps; one run emits both .ll and .s. Regenerated
# when the generator .py changes, so an edit is never silently linked from stale IR.
$(TVM_LL) $(TVM_S): $(GENERATOR_PY)
	$(MAKE) -C $(ARA_DIR)/tvm-apps tvm-ir app=$(name) nr_lanes=$(nr_lanes) nr_clusters=$(nr_clusters) config=$(config)

tvm-ir:
	$(MAKE) -C $(ARA_DIR)/tvm-apps tvm-ir app=$(name) nr_lanes=$(nr_lanes) nr_clusters=$(nr_clusters) config=$(config)

ifeq ($(tvm_codegen),asm)
$(BUILD_OBJS): $(TVM_S) | $(APP_OBJ_DIR) $(APP_LOG_DIR)
	@set -o pipefail; { \
	  echo "=== assemble TVM object (from .s) $$(date -Iseconds) ==="; \
	  echo "cmd: $(RISCV_CC) $(RISCV_CCFLAGS) -c $< -o $@"; \
	  $(RISCV_CC) $(RISCV_CCFLAGS) -c $< -o $@; \
	} 2>&1 | tee -a $(APP_LOG_DIR)/compile.log; exit $${PIPESTATUS[0]}
else
$(TVM_COMPAT): $(TVM_LL) | $(APP_OBJ_DIR) $(APP_LOG_DIR)
	@set -o pipefail; { \
	  echo "=== compat-strip $$(date -Iseconds) ==="; \
	  echo "cmd: sed 's/ nocreateundeforpoison//g' $< > $@"; \
	  sed 's/ nocreateundeforpoison//g' $< > $@; \
	} 2>&1 | tee -a $(APP_LOG_DIR)/compile.log; exit $${PIPESTATUS[0]}

$(BUILD_OBJS): $(TVM_COMPAT) | $(APP_OBJ_DIR) $(APP_LOG_DIR)
	@set -o pipefail; { \
	  echo "=== compile TVM object (from .ll) $$(date -Iseconds) ==="; \
	  echo "cmd: $(RISCV_CC) $(RISCV_CCFLAGS) -x ir -c $< -o $@"; \
	  $(RISCV_CC) $(RISCV_CCFLAGS) -x ir -c $< -o $@; \
	} 2>&1 | tee -a $(APP_LOG_DIR)/compile.log; exit $${PIPESTATUS[0]}
endif
