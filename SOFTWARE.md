# Software Setup: TVM and TileLang

This guide covers the **compiler software stack** used to generate code for AraXL:
[Apache TVM](https://tvm.apache.org/) and, optionally,
[TileLang](https://github.com/tile-ai/tilelang). It is separate from the
hardware/toolchain bootstrap described in [`README.md`](README.md) — do that
first (clone, branch, `./scripts/get-started.sh`), then return here.

These tools drive the TVM apps pipeline under
[`tvm-apps/`](tvm-apps/README.md):

```
TVM (Relax/TIR) → LLVM IR → AraXL riscv-clang → bare-metal ELF → Verilator sim
```

> Throughout this document, replace placeholders such as `<repo-root>`,
> `<path-to-tvm>`, and `<path-to-tilelang>` with the actual locations on your
> machine. Do **not** copy paths verbatim.

---

## 1. Conda environment

The TVM pipeline runs inside a [Conda](https://docs.conda.io/) environment so
that its Python, LLVM, and build dependencies stay isolated from the system and
from the hardware toolchain.

### Install Conda/Mamba (if you don't have it)

Any Conda distribution works. [Miniforge](https://github.com/conda-forge/miniforge)
is the recommended choice — it is community-built, defaults to the `conda-forge`
channel, and **bundles [`mamba`](https://mamba.readthedocs.io/)**, a much faster
drop-in replacement for the `conda` command:

```bash
# Linux x86_64 — see the Miniforge README for other platforms
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh
# restart your shell, then verify:
conda --version
mamba --version   # available with Miniforge
```

> Wherever this guide shows `conda`, you can substitute `mamba` (e.g.
> `mamba create`, `mamba install`) for faster solves. The two share the same
> environments and flags. The `tvm-apps` Makefile invokes the env via
> `conda run`, which works regardless of whether you created it with `conda` or
> `mamba`; if you prefer, set `TVM_PYTHON := mamba run -n tvm-dev python` in
> `local.mk`.

### Create the environment

This project refers to the environment as **`tvm-dev`**. Create it with a recent
Python (use `mamba` in place of `conda` if you prefer):

```bash
mamba create -n tvm-dev python=3.11    # or: conda create -n tvm-dev python=3.11
```

> **Important — use `conda run`, not `conda activate`.**
> `conda activate` does not work in non-interactive shells (scripts, `make`,
> CI). All tooling in this repo invokes the environment as:
>
> ```bash
> conda run -n tvm-dev <command>
> ```
>
> The `tvm-apps` Makefile already does this for you via the `TVM_PYTHON`
> variable (see [Section 4](#4-wire-it-into-tvm-apps)). When working
> interactively in your own terminal, `conda activate tvm-dev` is fine.

---

## 2. Apache TVM

The pipeline requires TVM **built from source with the LLVM backend enabled**
(it emits LLVM IR for the AraXL RISC-V toolchain). The prebuilt PyPI wheels are
not sufficient.

1. **Read the upstream install guide first:**
   <https://tvm.apache.org/docs/install/from_source.html>
2. **Clone and build** TVM into a location of your choice (`<path-to-tvm>`),
   following the upstream instructions, with the LLVM backend enabled in
   `config.cmake`. Build into the `tvm-dev` environment.
3. **Install the Python bindings** into the `tvm-dev` env (editable install from
   the TVM `python/` directory, per the upstream guide).
4. **Verify** the build:

   ```bash
   conda run -n tvm-dev python -c "import tvm; print(tvm.__version__)"
   ```

After building, TVM is referenced through three paths (the `tvm-apps` Makefile
derives the library/Python paths from `TVM_HOME`):

| Variable | Value |
|----------|-------|
| `TVM_HOME` | `<path-to-tvm>` (the source tree root) |
| `TVM_LIBRARY_PATH` | `<path-to-tvm>/build/lib` |
| `PYTHONPATH` | includes `<path-to-tvm>/python` |

> **TODO (maintainer):** this project has been developed against TVM `0.25.dev0`
> built from source. Document the exact TVM commit and the specific `config.cmake`
> LLVM settings it was validated against, so new users reproduce a known-good
> build rather than tracking upstream `main`.

### LLVM version note

The AraXL RISC-V toolchain (`riscv-clang`) and TVM's bundled LLVM can be
**different major versions**. The `tvm-apps` Makefile already strips
forward-incompatible IR attributes so the two interoperate; if a future LLVM
upgrade introduces a new unknown attribute, extend the IR-compatibility step in
[`tvm-apps/Makefile`](tvm-apps/Makefile). You do not need to do anything for the
default setup.

---

## 3. TileLang (optional)

[TileLang](https://github.com/tile-ai/tilelang) is a tile-level kernel DSL used
for kernel experiments that feed C/LLVM into the AraXL build pipeline. It is
**optional** — you do not need it to build and simulate the default kernels.

If you want it:

1. Read the upstream install guide:
   <https://github.com/tile-ai/tilelang> (see its `docs/get_started/`).
2. TileLang is GPU-focused but has a working CPU code-generation path; GPU
   execution requires a GPU-enabled host.
3. Install it into its **own** Conda environment (keep it separate from
   `tvm-dev`, since TileLang bundles its own TVM):

   ```bash
   conda create -n tilelang python=3.11
   # then follow the upstream build/install steps in <path-to-tilelang>
   ```

> **TODO (maintainer):** document the exact TileLang version and any local build
> patches required on this site's compilers once the TileLang → AraXL path is
> finalized.

---

## 4. Wire it into `tvm-apps`

Machine-specific paths live in `tvm-apps/local.mk`, which is **gitignored** and
loaded automatically by the Makefile. Copy the template and edit it:

```bash
cd <repo-root>/tvm-apps
cp local.mk.example local.mk
```

Set at least `TVM_HOME` in `local.mk`:

```makefile
# tvm-apps/local.mk
TVM_HOME   := <path-to-tvm>
TVM_PYTHON := conda run -n tvm-dev python
```

Verify the paths resolve before building:

```bash
make show-artifacts app=dotproduct
```

You are now ready to build and simulate — continue in
[`tvm-apps/README.md`](tvm-apps/README.md).
