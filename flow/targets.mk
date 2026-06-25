# targets.mk — simulator-binary builds (verilate/compile-vcs) + inspection,
# results, and housekeeping targets. The core build/run flow lives in the
# providers/*.mk + sim-run.mk; everything standalone is here.

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
	@$(ARTIFACTS_PYTHON) $(ARTIFACTS) report --run-dir "$(APP_SIM_RUN_DIR)" --app "$(app)"

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
	@echo "  spike:          $(SPIKE_BIN)  [$(if $(wildcard $(SPIKE_BIN)),present,MISSING)]  (c: provider only; opt: $(SPIKE_OPT))"
	$(if $(filter spike,$(simulator)),$(if $(filter-out 4,$(nr_lanes)),@echo "  NOTE: spike caps vlen at 4096; nr_lanes=$(nr_lanes) (config vlen may be wider) is NOT exercised at its true width on spike",))
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
	@$(ARTIFACTS_PYTHON) $(ARTIFACTS) status \
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
	@echo "  simulator=verilator|vcs|spike   config=NAME"
	@echo "      spike = functional RISC-V ISA-sim (correctness only, no timing); c: apps only"
	@echo "  nr_clusters=N           AraXL scaling knob (number of Ara2 clusters)"
	@echo "  nr_lanes=N              lanes/cluster — AraXL standard is 4; rarely change"
	@echo "  mem_latency / cva6_latency / ring_latency = cycles (require re-verilate)"
	@echo "  trace=0|1   sim_cycles=N   elf=<path> (prebuilt only)"
