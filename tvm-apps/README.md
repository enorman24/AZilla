# AraXL TVM Apps

TVM + AraXL integration workspace. Compiles TVM (Relax/TIR) models to bare-metal RISC-V ELFs and runs them on AraXL via Verilator simulation.

End-to-end pipeline: **TVM (Relax/TIR) → LLVM IR → AraXL riscv-clang → ELF → Verilator sim**

> **First time here?** Complete the toolchain bootstrap in the
> [top-level README](../README.md) and the TVM/TileLang setup in
> [`SOFTWARE.md`](../SOFTWARE.md) before running anything below. Then do the
> [one-time setup](#one-time-setup-localmk) in this directory.

---

## Quick start

```bash
# From AZilla/tvm-apps/

# One-time: build the Verilator simulator binary (slow; see below)
make verilate

# Generate LLVM IR
make tvm-ir app=fdotproduct

# Cross-compile → ELF
make compile app=fdotproduct

# Run Verilator sim (auto-starts live monitor in background)
make sim app=fdotproduct

# Watch live monitor output
make monitor app=fdotproduct
# or for the most recent run of any app:
make monitor-latest app=fdotproduct
```

The sections below explain each step, the configuration files, and how to debug
with waveforms. Run `make help` to list all targets.

---

## One-time setup: `local.mk`

Machine-specific paths live in `local.mk`, which is **gitignored** and loaded
automatically by the Makefile. Copy the template and edit it once:

```bash
# From AZilla/tvm-apps/
cp local.mk.example local.mk
```

Set at least `TVM_HOME` to your TVM source tree (see [`SOFTWARE.md`](../SOFTWARE.md)):

```makefile
# local.mk
TVM_HOME   := <path-to-tvm>
TVM_PYTHON := conda run -n tvm-dev python
```

Verify the resolved paths before building:

```bash
make show-artifacts app=fdotproduct
```

### Hardware configuration: `config.mk`

`config.mk` holds the non-machine-specific defaults — which app to build and the
hardware geometry. The defaults are:

| Setting | Default | Notes |
|---------|---------|-------|
| `app` | `fdotproduct` | Kernel under `kernels/` or model under `models/` |
| `config` | `default` | Hardware config file from `AZilla/config/<config>.mk` |
| `nr_clusters` | `2` | Number of Ara clusters |
| `nr_lanes` | `4` | Lanes per cluster |
| `mem_latency` | `0` | Memory latency in cycles (0 = ideal); requires re-verilate |
| `cva6_latency` | `0` | CVA6 latency in cycles; requires re-verilate |
| `ring_latency` | `0` | Ring interconnect latency in cycles; requires re-verilate |
| `simulator` | `verilator` | `vcs` is also supported (see [Debugging](#debugging-with-vcs-and-verdi)) |
| `sim_cycles` | *(empty)* | Stop after N simulated cycles; empty = run to program exit |
| `trace` | `0` | Verilator FST waveform tracing; requires `make verilate trace=1` |
| `verilate_jobs` | `8` | Parallel compile jobs for `make verilate` |
| `verilate_threads` | `8` | Runtime threads baked into the Verilator binary |

So the default build is a **2-cluster × 4-lane (8-lane) AraXL**. The cluster/lane
counts are baked into the Verilator binary at compile time — changing them
requires re-running `make verilate`. Any setting can be overridden on the command
line, e.g. `make sim app=fdotproduct nr_clusters=4`.

---

## Pipeline and app layout

All build outputs live under `build/` (not a separate `artifacts/` tree). The
Makefile is the single entry point; Python generators are invoked by `make tvm-ir`.

### `pipeline/` — models and build metadata

| File | Role |
|------|------|
| `pipeline/runner.py` | Model pipeline: Relax export → DPL pass → zero pipeline → LLVM IR |
| `pipeline/dpl_pass.py` | DPL `rewrite_call` pass — `inject_custom_kernels` |
| `pipeline/kernels.json` | Extern-kernel catalog: C symbol, source path, ABI, match rules |
| `pipeline/kernels_config.py` | Catalog loader (`KernelDef`, `KernelRule`, shape inference) |
| `pipeline/extern_primfunc.py` | `make_extern_primfunc()` helpers for `T.call_extern` wrappers |
| `pipeline/artifacts.py` | `manifest.json`, `pipeline.json`, `make audit` / `make report` |

**Models** (`models/<app>/<app>.py`) are built via:

```bash
make tvm-ir app=<model>    # invokes python -m pipeline.runner --app <model>
make compile app=<model>
make sim app=<model>
```

**Kernels** (`kernels/<app>/<app>.py`) are built via:

```bash
make tvm-ir app=<kernel>   # invokes python -m kernels.<app>.<app>
make compile app=<kernel>
make sim app=<kernel>
```

### Available apps

| Kind | App | Notes |
|------|-----|-------|
| kernel | `dotproduct` | Scalar TVM dot product (alternate example) |
| kernel | `fdotproduct` | Float dot product via extern C kernel (**default**) |
| kernel | `model_with_extern` | Small kernel exercising the extern-kernel path |
| model | `tiny_mlp` | 2-layer MLP; working end-to-end extern-kernel path |
| model | `quick_start` | Larger MLP export experiment |
| model | `conv2d_model` | Conv2D Relax model |
| model | `pytorch_import` | PyTorch → Relax import (`import_from_pytorch_model.py`; standalone, not wired to `make tvm-ir`) |

Extern C kernels are listed in `pipeline/kernels.json` and linked via per-app
`deps.mk` (`KERNEL_DEPS` → `build/lib/libaraxl_kernels.a`).

---

## Build the Verilator simulator

Before the first simulation (and after any change to `nr_clusters`, `nr_lanes`,
or the latency settings) build the Verilator binary for your configuration:

```bash
# From AZilla/tvm-apps/  — builds the default 2-cluster, 4-lane binary
make verilate
```

> **This step is slow** — it compiles the entire RTL design and can take many
> minutes to over an hour depending on the machine and configuration. **Run it
> inside [`tmux`](https://github.com/tmux/tmux/wiki)** so it survives an SSH
> disconnect (`tmux` to start, `Ctrl-b d` to detach, `tmux attach` to return).

The binary is reused across runs, so you only verilate once per configuration.

---

## Simulate a kernel

With the simulator built, building and running a kernel is quick:

```bash
# From AZilla/tvm-apps/
make sim app=fdotproduct
```

`make sim` automatically runs `tvm-ir` and `compile` as needed, then launches the
Verilator simulation. Compared to `make verilate`, this is fast (seconds to a few
minutes for small kernels).

> **Use Verilator for benchmarking and kernel testing.** It is significantly
> faster than VCS and needs no commercial license, so it is the recommended
> simulator for day-to-day correctness and performance work. Use VCS/Verdi only
> when you need waveform-level debugging (see below).

### If a simulation hangs or fails

Each run writes its artifacts and logs under `build/<app>/`:

| Location | Contents |
|----------|----------|
| `build/<app>/manifest.json` | Build manifest (tools, paths, target triple) |
| `build/<app>/pipeline.json` | Machine-readable pipeline stage graph |
| `build/<app>/00_codegen/ir/` | Numbered IR dumps for each pipeline stage |
| `build/<app>/00_codegen/final/` | Final `.ll` / `.s` from codegen |
| `build/<app>/02_link/` | Linked ELF and `.dump` (objdump) |
| `build/<app>/03_sim/runs/<RUN_ID>/` | Per-run sim output (`sim.log`, instruction trace, waveform) |
| `build/<app>/03_sim/runs/<RUN_ID>/inputs/` | Snapshot of ELF, IR, `main.c`, manifests for reproducibility |
| `build/<app>/03_sim/runs/<RUN_ID>/live.log` | Live sim monitor output (also tailed by `make monitor`) |
| `build/<app>/03_sim/latest/` | Symlink to the most recent run |
| `build/<app>/logs/<RUN_ID>/` | `verilate.log`, `compile-vcs.log`, build logs |

Utility targets (artifact root is always `build/`):

| Target | Purpose |
|--------|---------|
| `make audit app=<app>` | Regenerate `pipeline.json` and per-app README (no full build) |
| `make report app=<app>` | Print sim run summary (`RUN_ID=...` or latest) |
| `make check-symbols app=<app>` | Verify expected kernel symbols are present in the ELF |

When a run stalls, check `build/<app>/03_sim/latest/sim.log` and the decoded
instruction trace (`trace_hart_00.log`) in the same directory to see where it
stopped. **Please inspect these before asking for help** — they usually show the
exact PC/instruction where the sim got stuck. See the
[Known issues](#known-issues--araxl-kernel-simulation-stalls) section for an
example of diagnosing a stall.

---

## Debugging with VCS and Verdi

For deep debugging and waveform inspection, use Synopsys **VCS** (to simulate) and
**Verdi** (to view waveforms). This requires the commercial tools on your `PATH`
and a valid license. These are **not** hardcoded in the repo — source your site's
EDA setup script first so `VCS_HOME`, `LM_LICENSE_FILE`, and the VCS/Verdi
binaries are present in your shell environment, and the Makefile inherits them
automatically.

```bash
# From AZilla/tvm-apps/

# 1. Build the VCS simulator binary (slow — run in tmux)
make compile-vcs

# 2. Run the sim under VCS; this writes an FSDB waveform into the run directory
make sim app=fdotproduct simulator=vcs

# 3. Open the resulting waveform in Verdi
make view-sim app=fdotproduct
```

`make view-sim` opens Verdi on the FSDB from the most recent run (via the
`latest` symlink). To view a specific older run, pass its run id:
`make view-sim app=fdotproduct RUN_ID=<run_id>`. If no FSDB exists yet, the target
prints a note and exits without doing anything.

> **Note:** FSDB waveforms are produced only by VCS runs, not by Verilator runs.

> **The VCS binary is per-configuration.** Like the Verilator binary, the VCS
> simulator is built for a specific `nr_clusters` × `nr_lanes` geometry
> (`make compile-vcs` produces `hardware/build-vcs-nc<C>-l<L>/`). A VCS binary
> built for one configuration is **not** reused for another, and it is separate
> from the Verilator binary — so a config that already has a Verilator binary
> may have no VCS binary yet. Run `make compile-vcs` for the exact config you
> want to debug (matching the `nr_clusters`/`nr_lanes` you pass to `sim` and
> `view-sim`), or pass the config explicitly, e.g.
> `make compile-vcs nr_clusters=4` then
> `make sim app=fdotproduct simulator=vcs nr_clusters=4`.

### Viewing the GUI over VNC

Verdi is a graphical tool, so you need a GUI session on the server. The usual
approach is **VNC**: start a VNC server on the remote machine and connect to it
from your laptop with a VNC viewer (for example
[TigerVNC](https://tigervnc.org/) or [MobaXterm](https://mobaxterm.mobatek.net/) —
any VNC viewer works). Then, **from a terminal inside the VNC session**:

```bash
cd <repo-root>/tvm-apps
make view-sim app=fdotproduct
```

Launching `view-sim` from within the VNC desktop ensures Verdi can open its
windows. If Verdi fails to start, confirm the EDA tools are on your `PATH` and
your license server is reachable (see the tool setup for your environment).

---

## AraXL kernel status and validation requirements

**Before doing further TVM integration work, the AraXL kernels used by the extern-kernel pipeline must be refreshed and validated.**

The kernels under `AZilla/apps/` (`fmatmul`, `fbiasadd`, `fconv2d`, etc.) live in
this AZilla fork and may lag behind upstream
[predator2k/AraXL](https://github.com/predator2k/AraXL). Steps required:

1. **Sync or compare** kernel sources from upstream predator2k/AraXL into
   `AZilla/apps/`, or validate the copies already here against upstream.
2. **Test every kernel through the AraXL bare-metal pipeline** — using the
   standard AraXL benchmark harness (`AZilla/apps/<kernel>/`), NOT the TVM
   pipeline — to validate correctness on Verilator before integrating with TVM.
   Hardware-level bugs (dispatch logic, hazard handling, instruction sequencing)
   will not surface in host-Python testing.
3. Only after a kernel passes bare-metal validation should it be wired into the
   extern-kernel pipeline via `pipeline/kernels.json` and per-app `deps.mk`.

---

## Known issues — AraXL kernel simulation stalls

These issues were found during `tiny_mlp` end-to-end testing (model: x(4,16) → Linear(32) → ReLU → Linear(8), config: nc=4, nl=4).

### 1. fmatmul32 dispatch ignores M — FIXED

**File:** `AZilla/apps/fmatmul/kernel/fmatmul32.c`

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
1. Build a trace-enabled Verilator binary first: `make verilate trace=1` (once per
   hardware config). Then run `make sim app=tiny_mlp trace=1` — Verilator writes
   **FST** waveforms (not VCD) into the run directory. Inspect Ara queue fill
   level and scoreboard state around cycle 36949.
2. Write a minimal standalone C test that calls `fmatmul32(c, a, b, 4, 32, 8)` in isolation and run it under Verilator to confirm the stall is reproducible outside the TVM pipeline.
3. Check whether the AraXL `fmatmul` benchmark test suite covers `P=8` with `M=4` — if not, this parameter combination may never have been validated.
4. Try nc=2, nl=4 (default config) to see if the stall is cluster-count-dependent.
5. Compare against the latest upstream `fmatmul32_vec_4x4` source in predator2k/AraXL — the version in `AZilla/apps/` may predate a bug fix.

---

## TVM workspace allocator — required for fused kernels

Any `*_main.c` that calls a fused TVM kernel (one where FuseTIR inlines scalar ops like weight transposes alongside `call_extern`) **must** wire `__TVMBackendAllocWorkspace` / `__TVMBackendFreeWorkspace` before the first kernel call. If these are left null, the kernel returns -1 immediately and the sim exits with a non-zero `tohost` before any compute runs.

See `models/tiny_mlp/tiny_mlp_main.c`, `models/quick_start/quick_start_main.c`, or
`models/common/tvm_harness.h` for the standard pattern and sizing guidance.
