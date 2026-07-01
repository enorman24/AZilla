# verif.mk - RVV 1.0 + RV64 ground-up instruction verification suite.
# Included by flow/Makefile. Drives gen_kernels.py -> run_sweep.sh -> merge.py.
# Config is hardcoded to the 4-lane/4-cluster Verilator build but every knob is
# overridable (nr_lanes/nr_clusters come from flow config.mk; default 4/4).
#
# Targets:
#   make verif-gen   GROUPS="rvv-int-arith ..."   # (re)generate kernels for groups
#   make verif-run   GROUP=rvv-int-arith           # run one group  (<=VERIF_JOBS sims)
#   make verif-run   KERNEL=path/to/k.c            # run one kernel
#   make verif-run   FAILED=1                       # re-run all non-PASS kernels
#   make verif-class CLASS=rvv-int                  # gen + run + merge one class
#   make verif-merge                                # rebuild master.{json,csv,md}
#   make verif-status                               # print master.md summary
#   make verif                                      # full sweep (all classes)
#   make verif-clean                                # remove build/ (keep kernels)

VERIF_DIR     := $(FLOW_DIR)/verif
VERIF_SCRIPTS := $(VERIF_DIR)/scripts
VERIF_JOBS    ?= 3
VERIF_CYCLE_CAP ?= 200000
VERIF_WALL    ?= 350

# class -> inventory groups
CLASS_rvv-int  := rvv-int-arith rvv-int-logical rvv-int-shift rvv-int-narrow \
                  rvv-int-minmax rvv-int-cmp rvv-int-merge rvv-int-carry \
                  rvv-int-ext rvv-int-mul rvv-int-div rvv-int-muladd rvv-int-widen
CLASS_rvv-fp   := rvv-fp-arith rvv-fp-muladd rvv-fp-unary rvv-fp-minmax \
                  rvv-fp-sgnj rvv-fp-cmp rvv-fp-merge rvv-fp-cvt rvv-fp-widen rvv-fp-scalar
CLASS_rvv-red  := rvv-red-int rvv-red-fp
CLASS_rvv-mask := rvv-mask-logical rvv-mask-pop rvv-mask-set rvv-mask-iota rvv-mask-xmv
CLASS_rvv-perm := rvv-perm
CLASS_rvv-mem  := rvv-mem-unit rvv-mem-strided rvv-mem-indexed rvv-mem-whole rvv-mem-segment
CLASS_rvv-cfg  := rvv-config
CLASS_rv64     := rv64-scalar rv64i-reg rv64i-imm rv64i-word rv64i-load rv64i-store \
                  rv64i-branch rv64i-jump rv64i-sys rv64m rv64a rv64f-mem rv64f-arith \
                  rv64f-fma rv64f-misc rv64f-cvt rv64d-mem rv64d-arith rv64d-fma \
                  rv64d-misc rv64d-cvt zicsr
ALL_CLASSES    := rvv-int rvv-fp rvv-red rvv-mask rvv-perm rvv-mem rvv-cfg rv64

GROUPS ?=
CLASS  ?=
GROUP  ?=
KERNEL ?=
FAILED ?=

.PHONY: verif verif-gen verif-run verif-merge verif-class verif-status verif-clean

verif-gen:
	@python3 $(VERIF_SCRIPTS)/gen_kernels.py --groups $(GROUPS)

verif-run:
	@bash $(VERIF_SCRIPTS)/run_sweep.sh \
	  $(if $(strip $(KERNEL)),--kernel $(KERNEL),) \
	  $(if $(strip $(GROUP)),--groups "$(GROUP)",) \
	  $(if $(strip $(FAILED)),--failed-only,) \
	  --jobs $(VERIF_JOBS) --cycle-cap $(VERIF_CYCLE_CAP) --wall $(VERIF_WALL) \
	  --nr-lanes $(nr_lanes) --nr-clusters $(nr_clusters) --ara-dir $(ARA_DIR)

verif-merge:
	@python3 $(VERIF_SCRIPTS)/merge.py

# gen + run + merge for one class (CLASS=rvv-int|rvv-fp|...)
verif-class:
	@test -n "$(CLASS)" || { echo "set CLASS= (one of: $(ALL_CLASSES))"; exit 1; }
	@python3 $(VERIF_SCRIPTS)/gen_kernels.py --groups $(CLASS_$(CLASS))
	@bash $(VERIF_SCRIPTS)/run_sweep.sh --groups "$(CLASS_$(CLASS))" \
	  --jobs $(VERIF_JOBS) --cycle-cap $(VERIF_CYCLE_CAP) --wall $(VERIF_WALL) \
	  --nr-lanes $(nr_lanes) --nr-clusters $(nr_clusters) --ara-dir $(ARA_DIR)
	@python3 $(VERIF_SCRIPTS)/merge.py
	@echo "class $(CLASS) done; see flow/verif/results/master.md"

# full sweep, class by class
verif:
	@for c in $(ALL_CLASSES); do $(MAKE) --no-print-directory verif-class CLASS=$$c; done

verif-status:
	@sed -n '1,40p' $(VERIF_DIR)/results/master.md 2>/dev/null || echo "no results yet; run a class first"

verif-clean:
	@rm -rf $(VERIF_DIR)/build/*/ && echo "cleaned verif build dirs (kernels kept)"
