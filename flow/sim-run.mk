# ════════════════════════════════════════════════════════════════════════════
#  flow/sim-run.mk — shared RUN layer (provider-agnostic).
#
#  Included by flow/Makefile. Depends on `provider-build` (which the orchestrator
#  defines per provider) having produced $(ELF). Drives scripts/run-sim.sh (the
#  actual run-management logic) and then emits manifest.json from the rc/start/
#  end/cmd the script captured. The manifest step lives here, not in the script,
#  because it needs the TVM conda env — kept in Make where that env is wired.
# ════════════════════════════════════════════════════════════════════════════

sim: provider-build
	@mkdir -p $(APP_SIM_RUN_DIR)/inputs
	@bash $(RUN_SIM) \
	  --ara-dir "$(ARA_DIR)" --simulator "$(simulator)" \
	  --elf "$(ELF)" --label "$(app)" \
	  --run-dir "$(APP_SIM_RUN_DIR)" --sim-dir "$(APP_SIM_DIR)" --run-id "$(RUN_ID)" \
	  --config "$(config)" --nr-clusters "$(nr_clusters)" --nr-lanes "$(nr_lanes)" \
	  --mem-latency "$(mem_latency)" --cva6-latency "$(cva6_latency)" --ring-latency "$(ring_latency)" \
	  --trace "$(trace_status)" --sim-cycle-arg "$(SIM_CYCLE_ARG)" \
	  --veril-binary "$(VERIL_BINARY)" \
	  --spike-bin "$(SPIKE_BIN)" --spike-opt "$(SPIKE_OPT)" \
	  --vcs-binary "$(VCS_BINARY)" --vcs-dpi "$(VCS_DPI_LIB)" --vcs-build-dir "$(VCS_BUILD_DIR)" --vcs-env "$(VCS_ENV)" \
	  --return-status "$(RETURN_STATUS)" \
	  --spike-dasm "$(SPIKE_DASM)" --monitor "$(MONITOR)" \
	  --snapshot "$(ELF)" \
	  --snapshot "$(TVM_LL)" --snapshot "$(TVM_S)" --snapshot "$(TVM_COMPAT)" --snapshot "$(BUILD_MAIN_C)" \
	  --snapshot "$(APP_DIR)/manifest.json" --snapshot "$(APP_DIR)/pipeline.json"; \
	rc=$$?; \
	$(ARTIFACTS_PYTHON) $(ARTIFACTS) sim-manifest \
	  --output "$(APP_SIM_RUN_DIR)/manifest.json" \
	  --app "$(app)" --run-id "$(RUN_ID)" --simulator "$(simulator)" \
	  --command "$$(cat $(APP_SIM_RUN_DIR)/.sim_cmd 2>/dev/null)" \
	  --cwd "$(APP_SIM_RUN_DIR)" --elf "$(ELF)" \
	  --verilator-binary "$(SIM_BINARY)" \
	  --return-code "$$(cat $(APP_SIM_RUN_DIR)/.sim_rc 2>/dev/null || echo $$rc)" \
	  --start-time "$$(cat $(APP_SIM_RUN_DIR)/.sim_start 2>/dev/null)" \
	  --end-time "$$(cat $(APP_SIM_RUN_DIR)/.sim_end 2>/dev/null)" \
	  --config "$(config)" --nr-clusters "$(nr_clusters)" --nr-lanes "$(nr_lanes)" \
	  --mem-latency "$(mem_latency)" --cva6-latency "$(cva6_latency)" --ring-latency "$(ring_latency)" \
	  --trace "$(trace_status)" --inputs-dir "$(APP_SIM_RUN_DIR)/inputs" \
	  --repro-env "TVM_HOME=$(TVM_HOME)" \
	  --repro-env "TVM_LIBRARY_PATH=$(TVM_LIBRARY_PATH)" \
	  --repro-env "PYTHONPATH=$(TVM_PYTHONPATH):$$PYTHONPATH" \
	  --repro-env "nr_clusters=$(nr_clusters)" --repro-env "nr_lanes=$(nr_lanes)" \
	  2>/dev/null || echo "flow: manifest emission skipped (artifacts.py unavailable)"; \
	$(ARTIFACTS_PYTHON) $(ARTIFACTS) ledger-append \
	  --manifest "$(APP_SIM_RUN_DIR)/manifest.json" --ledger "$(LEDGER)" 2>/dev/null \
	  || echo "flow: ledger append skipped"; \
	exit $$rc

$(APP_SIM_RUN_DIR):
	@mkdir -p $@
