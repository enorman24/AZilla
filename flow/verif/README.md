# AZilla RVV 1.0 + RV64 ground-up instruction verification

Directed, self-checking assembly tests that prove — instruction by instruction —
whether each RVV 1.0 and RV64 scalar instruction executes **correctly** on this
hardware (CVA6 + AraXL, NR_LANES=4 / NR_CLUSTERS=4 Verilator build). Built from
the ISA specs and the RTL, not from any prior documentation.

## Method (differential oracle)

Each kernel sets up deterministic inputs, runs the instruction under test as
explicit inline assembly, extracts the result, and prints it as raw hex bracketed
by markers. The **same** kernel body is built twice and run on two simulators:

- **Spike** (`install/riscv-isa-sim`, `--varch=vlen:4096,elen:64`) — the RISC-V
  architectural reference model. This is the **oracle** (golden output). Spike is
  functional-only: it does **not** reproduce AraXL hangs, so it gives the correct
  answer even when the RTL deadlocks.
- **AraXL Verilator** (`hardware/build-nc4-l4/.../Vara_tb_verilator`) — the DUT.

The two payloads are compared per-variant. Classification:

| Status | Meaning |
|---|---|
| `PASS` | Verilator printed `*** SUCCESS ***` and its result matches Spike bit-for-bit |
| `FAIL_INCORRECT` | completed but result differs from Spike (or a non-illegal trap) |
| `FAIL_HANG` | no banner within the cycle cap / wall timeout (deadlock/livelock/slow) |
| `BLOCKED` | illegal-instruction trap (mcause=2) while Spike runs fine — not decoded by AraXL |
| `UNTESTED` | a later variant in a kernel that stopped at an earlier trap/hang |

A **surprise** = observed status disagrees with the RTL-derived expectation
(supported→PASS, blocked_illegal→BLOCKED, blocked_silent→FAIL_INCORRECT). Surprises
are the actionable findings, listed at the top of `results/master.md`.

### Key constraints baked in
- AraXL architectural VLEN = 16384 (4 clusters x 4096) but Spike caps at vlen:4096,
  so every test's **AVL is clamped to VLMAX_spike(SEW,LMUL)** — both sims then
  process identical vl and data. VLEN-exposing CSRs (vlenb) are not cross-checked.
- Result extraction is always a unit-stride `vse` to a 128-byte-aligned `.l2`
  buffer (AraXL deadlocks on non-64B-aligned vector stores).
- Masked variants use mask-undisturbed with a preloaded destination; tail elements
  are not dumped (agnostic fill is implementation-defined). vl=0 uses tail-undisturbed.
- The console `_putchar` is ordered (fence/readback) because the stock `serial.c`
  drops coalesced MMIO byte stores.

## Layout

```
inventory/   inventory.{py,json,csv,md}   - the spec-derived instruction spine (400)
kernels/<group>/<mnem>.c (+ .meta.json)   - committed directed kernels (auditable)
kernels/verif.h                           - markers, FNV digest, dump helpers, _putchar
scripts/gen_kernels.py                    - inventory -> kernels (representative-broad)
scripts/verify_one.py                     - build both targets, emit IR, run both, classify
scripts/run_sweep.sh                      - run a group/class <= N sims concurrently
scripts/merge.py                          - per-kernel result.json -> master.{json,csv,md} + master_variants.csv
build/<group>/<mnem>/                      - per-kernel artifacts (gitignored): ELFs, .s + .dump IR, spike.out, sim.log, result.json
results/master*.{json,csv,md}              - the tracking log (Step 4 deliverable)
```

Per-kernel **IR** (Step 6) is emitted next to each build: `<mnem>.s` (clang
assembly) and `<mnem>.dump` (objdump disassembly showing the actual ratified RVV
1.0 encodings).

## Running (from `flow/`)

```bash
make verif-class CLASS=rvv-int      # generate + run + merge one class (rvv-int|rvv-fp|rvv-red|rvv-mask|rvv-perm|rvv-mem|rvv-cfg|rv64)
make verif-run   GROUP=rvv-int-arith        # run one inventory group
make verif-run   KERNEL=verif/kernels/rvv-int-arith/vadd.c   # one kernel
make verif-run   FAILED=1                    # re-run everything that did not PASS
make verif-merge                             # rebuild the master log
make verif-status                            # print the summary
make verif                                   # full sweep, class by class
```

Knobs: `VERIF_JOBS` (concurrent sims, default 3), `VERIF_CYCLE_CAP`,
`VERIF_WALL`, `nr_lanes`, `nr_clusters` (default 4/4).
