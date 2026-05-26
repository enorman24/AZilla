# AraXL TVM Apps

TVM + AraXL integration workspace. Compiles TVM (Relax/TIR) models to bare-metal RISC-V ELFs and runs them on AraXL via Verilator simulation.

End-to-end pipeline: **TVM (Relax/TIR) → LLVM IR → AraXL riscv-clang → ELF → Verilator sim**

See `CLAUDE.md` for full architecture, build commands, and environment setup.

---

## Quick start

```bash
# From AraXL/tvm-apps/

# Generate LLVM IR
make tvm-ir app=dotproduct

# Cross-compile → ELF
make compile app=dotproduct

# Run Verilator sim (auto-starts live monitor in background)
make sim app=dotproduct

# Watch live monitor output
make monitor app=dotproduct
# or for the most recent run of any app:
make monitor-latest app=dotproduct
```

---

## AraXL kernel status and validation requirements

**Before doing further TVM integration work, the AraXL kernels used by the extern-kernel pipeline must be refreshed and validated.**

The kernels under `AraXL/apps/` (`fmatmul`, `fbiasadd`, `fconv2d`, etc.) may not reflect the most up-to-date versions in the AraXL repository. Steps required:

1. **Pull the latest kernel sources** from the upstream AraXL repository into `AraXL/apps/`.
2. **Test every kernel through the AraXL bare-metal pipeline** — using the standard AraXL benchmark harness (`AraXL/apps/<kernel>/`), NOT the custom TVM pipeline — to validate correctness on Verilator before integrating with TVM. Hardware-level bugs (dispatch logic, hazard handling, instruction sequencing) will not surface in host-Python testing.
3. Only after a kernel passes bare-metal validation should it be wired into the extern-kernel pipeline via `kernels.json` and `deps.mk`.

---

## Known issues — AraXL kernel simulation stalls

These issues were found during `tiny_mlp` end-to-end testing (model: x(4,16) → Linear(32) → ReLU → Linear(8), config: nc=4, nl=4).

### 1. fmatmul32 dispatch ignores M — FIXED

**File:** `AraXL/apps/fmatmul/kernel/fmatmul32.c`

**Root cause:** The original `fmatmul32()` dispatch selected the kernel variant based only on `P` (the inner dimension / column count), ignoring `M` (the row count). `fmatmul32_vec_16x16` and `fmatmul32_vec_8x8` hardcode 16 and 8 scalar prefetch/store sequences respectively; calling them with `M < block_size` causes out-of-bounds reads and stores, producing incorrect results or a sim hang.

Concretely: with nc=4, nl=4, both matmuls in tiny_mlp have P ≤ 512 and were dispatched to `fmatmul32_vec_16x16`, even though M=4.

**Fix applied:** Dispatch now selects by both P (LMUL tier) and M (block size):

```c
if (P <= NR_LANES * NR_CLUSTERS * 32) {           // LMUL=1
    if (M >= 16) fmatmul32_16x16(...);
    else if (M >= 8) fmatmul32_8x8(...);
    else             fmatmul32_4x4(...);
} else if (P <= NR_LANES * NR_CLUSTERS * 32 * 2) { // LMUL=2
    if (M >= 8) fmatmul32_8x8(...);
    else        fmatmul32_4x4(...);
} else {                                            // LMUL=4
    fmatmul32_4x4(...);
}
```

### 2. fmatmul32_vec_4x4 stall on second matmul — UNRESOLVED

**Symptom:** After fixing issue #1, the sim stalls in `fmatmul32_vec_4x4` during the second matmul call (M=4, N=32, P=8). The stall occurs at the first inner loop iteration (PC `0x80003bd8`, `c.addi s7, 8`, cycle ~36949). No new dasm trace lines are produced after this point; CVA6 is blocking on the Ara instruction queue.

**Context:**
- 14 `vle32.v` dispatches were observed before the stall, confirming the first matmul (M=4, N=16, P=32) completed correctly.
- The second matmul uses VL=8, LMUL=4. The stall appears after 10 in-flight vector instructions (4×`vfmacc.vf` + `vle32.v` + 4×`vfmacc.vf` + `vle32.v`) without Ara draining.
- Likely cause: Ara instruction queue overflow or a WAW hazard the scoreboard does not drain correctly for this VL/LMUL combination. The 4x4 kernel reuses v0/v4/v8/v12 in successive iterations, which may interact poorly with Ara's in-flight tracking.

**Investigation steps:**
1. Run with `make sim app=tiny_mlp trace=1` to capture VCD waveforms; inspect Ara queue fill level and scoreboard state around cycle 36949.
2. Write a minimal standalone C test that calls `fmatmul32(c, a, b, 4, 32, 8)` in isolation and run it under Verilator to confirm the stall is reproducible outside the TVM pipeline.
3. Check whether the AraXL `fmatmul` benchmark test suite covers `P=8` with `M=4` — if not, this parameter combination may never have been validated.
4. Try nc=2, nl=4 (default config) to see if the stall is cluster-count-dependent.
5. Compare against the latest upstream `fmatmul32_vec_4x4` source — the version in `AraXL/apps/` may predate a bug fix.

---

## TVM workspace allocator — required for fused kernels

Any `*_main.c` that calls a fused TVM kernel (one where FuseTIR inlines scalar ops like weight transposes alongside `call_extern`) **must** wire `__TVMBackendAllocWorkspace` / `__TVMBackendFreeWorkspace` before the first kernel call. If these are left null, the kernel returns -1 immediately and the sim exits with a non-zero `tohost` before any compute runs.

See `models/tiny_mlp/tiny_mlp_main.c` or `CLAUDE.md` for the standard pattern and sizing guidance.
