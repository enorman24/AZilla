# flow — unified AraXL build + sim orchestrator

One entry point to build a kernel and run it on AraXL. You name an app as
`<provider>:<name>`, pick a simulator, and `flow` resolves/builds the ELF and runs
it through one shared run layer (per-run output dir, logs, live monitor, result
manifest + ledger) — identical UX for every provider and simulator.

> Part of the **AZilla** repo — not standalone. It references sibling dirs
> (`apps/`, `tvm-apps/`, `hardware/`, `config/`, `install/`) via the repo root, so
> run it inside a full AZilla checkout. Build the toolchain + simulators first with
> the top-level repo build (see the repo root `README.md`).

## Quickstart

```bash
# Build the Verilator RTL-sim binary once for your hardware config:
make verilate nr_clusters=2 nr_lanes=4

# Build a hand-written C kernel and run it on the RTL sim:
make sim app=c:dotproduct

# Or run it on Spike (functional RISC-V ISA-sim — fast correctness check):
make sim app=c:hello_world simulator=spike

# Discover what's available:
make list-apps        # runnable apps, by provider
make list-configs     # hardware configs (the config= knob)
make show-config app=c:dotproduct   # resolved paths/binaries for one app
make help             # all targets + knobs
```

**No TVM required for `c:` apps.** The `c` provider uses only the RISC-V toolchain
and a simulator binary — build, run, pass/fail, manifests, ledger and `make status`
all work with no TVM/conda installed. Only the `tvm:` provider needs the TVM env.

## Providers (`app=<provider>:<name>`)

| Provider | Source | Needs TVM? |
|----------|--------|-----------|
| `c`        | `apps/<name>/` (hand-written C kernels) | no |
| `tvm`      | `tvm-apps/{kernels,models}/<name>/`     | **yes** (conda env + TVM build) |
| `prebuilt` | any existing ELF — pass `elf=<path>`    | no |
| `tilelang` | *(planned, not yet implemented)*        | — |

## Simulators (`simulator=`)

| Value | What | Notes |
|-------|------|-------|
| `verilator` *(default)* | cycle-accurate AraXL RTL sim | needs `make verilate` first |
| `vcs` | cycle-accurate RTL sim on Synopsys VCS | needs a VCS license + `make compile-vcs` |
| `spike` | functional RISC-V ISA-sim (golden reference) | **`c:` apps only**; correctness, not timing |

## Common targets

```
make sim app=<id>          build (per provider) + run on the sim, full run UX
make verilate              build the shared Verilator binary for this config
make compile-vcs           build the shared VCS binary
make status                results matrix of all runs -> RESULTS.md (local only)
make report app=<id>       summarize the latest run
make monitor app=<id>      tail the live monitor for a run
make clean-build app=<id>  remove an app's build artifacts (keeps sim runs)
make distclean             remove all build artifacts + sim runs
```

## Key knobs (command line or `config.mk`)

```
app=<provider>:<name>     what to build/run
simulator=verilator|vcs|spike
config=<name>             hardware config (see `make list-configs`)
nr_clusters=N             AraXL scaling knob (number of Ara2 clusters)
nr_lanes=N                lanes/cluster — AraXL standard is 4; rarely change
trace=0|1                 RTL waveform tracing (needs `make verilate trace=1`)
elf=<path>                ELF to run (prebuilt provider only)
```

## Layout

```
Makefile             orchestrator: setup + the load-bearing include sequence (no rules)
config.mk            default knobs (override on the command line)
hw-config.mk         derived geometry + simulator-binary paths
providers/c.mk       \
providers/tvm.mk      } one file per provider: builds that provider's ELF
providers/prebuilt.mk/   (add a new provider = add a providers/<name>.mk)
build.mk             shared link→ELF layer (LLVM/RTL path)
sim-run.mk           shared run layer (drives run-sim.sh, emits manifest + ledger)
targets.mk           verilate/compile-vcs + inspection / results / cleanup targets
scripts/run-sim.sh   the actual ELF-agnostic sim runner (verilator|vcs|spike)
local.mk.example     copy to local.mk for machine-specific paths (gitignored)
build/               all build + sim outputs (gitignored)
results/             run ledger; RESULTS.md is the rendered matrix (gitignored)
```

The orchestrator reads `config.mk → local.mk → hw-config.mk`, then includes the
selected `providers/<provider>.mk`, then `build.mk` (only if the provider builds
through flow), `sim-run.mk`, and `targets.mk`. Each step defines what the next
consumes — the order is documented at the top of `Makefile`.

Machine-specific paths (TVM tree, Verilator/VCS install, license) go in a
`local.mk` you copy from `local.mk.example` — it is gitignored.
