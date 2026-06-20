# SRAM backends: public behavioral model vs. private GF12 hard macro

Both the **Ara vector register file (VRF)** banks and the **CVA6 L1 I$/D$ caches** can be
backed by one of two SRAM implementations, selected at compile time. The VRF lives in
this repo (`hardware/src/lane/vector_regfile.sv`); the caches live in the Bender-managed
`ariane` dep and are wired via a tracked patch (see "Bender dep patches" below). Both
funnel through the **same** neutral `gf12_vrf_bank` wrapper when hardened.

| Backend | When | Source | IP status |
|---------|------|--------|-----------|
| **`tc_sram`** (behavioral) | **Default** — every public build (Verilator and VCS/Questa) | PULP `tech_cells_generic` (Bender dep) | Open source |
| **`gf12_vrf_bank`** (GF12 hard macro) | Opt-in: `gf12_sram=1` | A private wrapper + foundry model, **not in this repo** | NDA — never committed here |

This repo is public. **No foundry-proprietary content lives in it** — not the macro
part number, not its pin names, not the model file, not PDK paths. The hardened path
is a clean opt-in that pulls those files from a private location you point it at.

## How the seam works

`vector_regfile.sv` instantiates one of two modules per bank behind a define:

```systemverilog
`ifdef GF12_SRAM_MACRO
  gf12_vrf_bank #(.NumWords(NumWords), .DataWidth(DataWidth)) data_sram ( ... );
`else
  tc_sram      #(.NumWords(NumWords), .DataWidth(DataWidth), .NumPorts(1)) data_sram ( ... );
`endif
```

Both instances use the **same port list** (clk/rst/req/we/be/addr/wdata/rdata), so the
two backends are drop-in interchangeable. `GF12_SRAM_MACRO` is **off by default**; the
hardware Makefile defines it only when you pass `gf12_sram=1`, and at the same time adds
the private wrapper to the compile filelist (`+incdir+$(GF12_SRAM_DIR)` and an extra
`vlog`/`vlogan` of `$(GF12_SRAM_DIR)/*.sv`). Verilator always stays on `tc_sram`.

## The `gf12_vrf_bank` wrapper contract

A licensed user supplies a module named `gf12_vrf_bank` with exactly this interface
(it mirrors a single-port `tc_sram`; the wrapper internally drives the foundry macro):

```systemverilog
module gf12_vrf_bank #(
    parameter int unsigned NumWords  = 64,
    parameter int unsigned DataWidth = 64
  ) (
    input  logic                   clk_i,
    input  logic                   rst_ni,
    input  logic                   req_i,
    input  logic                   we_i,
    input  logic [DataWidth/8-1:0] be_i,
    input  logic [$clog2(NumWords)-1:0] addr_i,
    input  logic [DataWidth-1:0]   wdata_i,
    output logic [DataWidth-1:0]   rdata_o
  );
```

The wrapper and the generated SRAM model are maintained in the private GF12 flow repo
(e.g. `gf12_flow_ssrl/sram/integration/`), which is the single source of truth for them.

## CVA6 I$/D$ caches use the same wrapper

The caches (`cva6_icache`, `wt_dcache_mem`) reach SRAM through CVA6's `sram` →
`tc_sram_wrapper` chain. `tc_sram_wrapper` carries the same `` `ifdef GF12_SRAM_MACRO``
seam, and when hardened it instantiates the **same** `gf12_vrf_bank` wrapper (default:
`tc_sram`). For the `cv64a6_imafdcv_sv39` config (I$ 4 KiB/4-way/128 b, D$ 8 KiB/4-way/
256 b WT) every cache cut resolves to **64 words × 64 bits, single-port, byte-enable** —
identical geometry to the VRF bank — so one macro cut covers VRF and caches alike.

This seam lives in the Bender-managed `ariane` dep, so it is applied via a tracked patch
(below), not stored as repo source. Changing cache size/assoc/line width can make
`NUM_WORDS ≠ 64`, which would need a different macro cut.

## Running the public build (no IP, default)

```bash
cd tvm-apps
conda run -n tvm-dev make tvm-ir compile app=<app>   # build the ELF
make compile-vcs                                      # builds simv on tc_sram
make sim simulator=vcs app=<app>                      # run -> expect PASS
```

(Verilator works the same way via `make verilate` / `make sim simulator=verilator`.)

## Reproducing the private GF12-hardened build

You need: (1) a checkout of the private GF12 flow repo containing
`sram/integration/gf12_vrf_bank.sv` and the foundry model, and (2) the PDK if you go on
to synthesis.

1. Point the build at the private integration dir. Create `hardware/local.mk`
   (gitignored — copy from `hardware/local.mk.example`):
   ```make
   GF12_SRAM_DIR := /path/to/gf12_flow_ssrl/sram/integration
   ```
2. Build and run on VCS with the opt-in flag:
   ```bash
   cd tvm-apps
   make compile-vcs gf12_sram=1
   make sim simulator=vcs app=<app>
   ```

If you pass `gf12_sram=1` without setting `GF12_SRAM_DIR`, the build stops with a clear
error telling you what to set.

## Bender dep patches (required on a fresh clone)

`hardware/deps/` is Bender-managed and gitignored, so changes to those deps are **not**
stored as source — they are kept as patches under `hardware/patches/` and applied with:

```bash
cd hardware && make apply-patches      # idempotent: skips patches already applied
```

| Patch | Dep | What it adds | IP? |
|-------|-----|--------------|-----|
| `0001-tech-cells-generic-sram.patch` | `tech_cells_generic` | `tc_sram` `InitFromFile`/`MemInitFile` (DRAM `$readmemh` preload) + Verilator write/memory-loader. **Required** — tracked `ara_soc.sv` depends on it. | No |
| `0002-ariane-araxl.patch` | `ariane` (cva6) | `tc_sram_wrapper` GF12 seam (neutral `gf12_vrf_bank`, inert unless `gf12_sram=1`) + `DISABLE_INSTR_TRACER` guard | No |

Both patches are IP-free and safe to apply on any (public) checkout — the GF12 seam is
inert until `gf12_sram=1`. Regenerate a patch after editing a dep with
`git -C hardware/deps/<dep> diff <files> > hardware/patches/<name>.patch`. Run
`make apply-patches` after every fresh `bender checkout`/`update`, or it will be lost.

## Never commit to this repo

The following must stay out of AraXL (the `.gitignore` enforces a safety net):

- The foundry SRAM model (any vendor memory `*.v`)
- The `gf12_vrf_bank.sv` wrapper (lives in the private flow repo)
- `hardware/local.mk` (your local paths)
- PDK paths, license servers, and any file carrying a vendor "Confidential" header

Pre-push sanity checks (should print nothing):

```bash
# 1) no PDK paths, personal paths, or vendor headers in the RTL/build files
git grep -ni 'confidential\|/mnt/ssd\|/home/' -- hardware/src hardware/Makefile
# 2) the private wrapper / vendor model files are not tracked
git ls-files | grep -E 'gf12_vrf_bank\.sv|/IN12LP|local\.mk$' || echo "clean"
```
