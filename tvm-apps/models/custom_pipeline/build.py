"""End-to-end build entry point for the custom kernel pipeline.

Flow:

    1. Define / import a Relax model (here: tiny conv2d-only example).
    2. Load ``kernels.json`` -> list[KernelSpec].
    3. Run the custom pass to rewrite matched ops into ``call_tir`` /
       ``call_extern`` invocations.
    4. Lower with a normal Relax pipeline.
    5. Build for the chosen target:

       - Host shared library:  ``tvm.compile`` + ``Executable.export_library``
         with an ``fcompile`` that compiles & links the listed C files.
       - AraXL / bare-metal:    emit LLVM IR ``.ll`` (matches the existing
         ``tvm-apps/Makefile`` flow); the Makefile then compiles ``.ll``
         and the listed C files with the RISC-V toolchain.

Run::

    python -m tvm-apps.models.custom_pipeline.build           # host build
    python -m tvm-apps.models.custom_pipeline.build --araxl   # emit .ll
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, List

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from kernels_config import KernelSpec, load_kernels  # type: ignore
    from custom_pass import replace_with_extern_kernels  # type: ignore
else:
    from .kernels_config import KernelSpec, load_kernels
    from .custom_pass import replace_with_extern_kernels

import tvm
from tvm import relax
from tvm.relax.frontend import nn


HERE = Path(__file__).resolve().parent
TVM_APPS_DIR = HERE.parent.parent
ARA_DIR = TVM_APPS_DIR.parent
DEFAULT_JSON = HERE / "kernels.json"


class Conv2DOnly(nn.Module):
    """Tiny model whose only op is the one we want to swap out.

    Sized + typed to match ``apps/fconv2d/fconv2d_3x3.c``:

      - FP64 (the AraXL kernel takes ``double*``).
      - Single channel, single batch.
      - The AraXL kernel does NOT pad internally; it expects the input
        to be pre-padded to ``(R+F-1) x (C+F-1)``. We therefore use
        ``padding=0`` and shape the input to ``1x1x18x18`` so the conv
        output (``target_shape`` in ``kernels.json``) is ``1x1x16x16``.
    """

    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2D(
            in_channels=1,
            out_channels=1,
            kernel_size=3,
            stride=1,
            padding=0,
            bias=False,
            dtype="float64",
        )

    def forward(self, x):
        return self.conv(x)


def build_relax_model() -> tvm.IRModule:
    mod, _params = Conv2DOnly().export_tvm(
        spec={"forward": {"x": nn.spec.Tensor((1, 1, 18, 18), "float64")}}
    )
    return mod


def make_fcompile(extra_sources: Iterable[str], extra_cflags: List[str] | None = None):
    """Return an ``fcompile`` callable for ``export_library``.

    It compiles & links the TVM-generated object together with the
    handwritten C files listed in ``kernels.json``.  Use this for
    host targets where TVM owns the linker invocation.
    """
    from tvm.contrib import cc

    extra_sources = list(extra_sources)
    extra_cflags = list(extra_cflags or [])

    def fcompile(out_path, objects, options=None):
        opts = list(options or []) + extra_cflags
        all_inputs = list(objects) + extra_sources
        cc.create_shared(out_path, all_inputs, options=opts)

    return fcompile


def dump_ir(mod: tvm.IRModule, path: Path) -> Path:
    """Write ``mod.script()`` to ``path`` so you can diff stages by eye."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(mod.script(), encoding="utf-8")
    print(f"  -> {path}")
    return path


def dump_codegen(ex, out_dir: Path, stem: str) -> None:
    """Dump final LLVM IR + assembly from a compiled Executable."""
    llvm_mod = ex.mod.imports[0] if len(ex.mod.imports) else ex.mod
    ll_path = out_dir / f"{stem}.ll"
    s_path = out_dir / f"{stem}.s"
    ll_path.write_text(llvm_mod.inspect_source("ll"), encoding="utf-8")
    s_path.write_text(llvm_mod.inspect_source("asm"), encoding="utf-8")
    print(f"  -> {ll_path}")
    print(f"  -> {s_path}")


def _resolve_c_inputs(specs: List[KernelSpec]) -> tuple[List[str], List[str]]:
    """Resolve all .c source files and -I include dirs from the specs.

    Paths in ``kernels.json`` are interpreted relative to the AraXL repo
    root (``ARA_DIR``), so entries like ``apps/fconv2d/fconv2d_3x3.c`` map
    to ``/.../AraXL/apps/fconv2d/fconv2d_3x3.c``.
    """
    srcs: List[str] = []
    incs: List[str] = []
    for s in specs:
        for f in [s.source_file, *s.extra_sources]:
            srcs.append(str((ARA_DIR / f).resolve()))
        for d in s.include_dirs:
            incs.append(str((ARA_DIR / d).resolve()))
    return srcs, incs


def build_host(mod: tvm.IRModule, specs: List[KernelSpec], out_dir: Path) -> Path:
    """Build a host-side shared library that links the custom C kernels.

    AraXL kernels (RVV intrinsics, inline RISC-V asm, AraXL runtime
    deps) are not portable. Specs that set ``host_compatible: false``
    are rejected here with a clear message.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    riscv_only = [s for s in specs if not s.host_compatible]
    if riscv_only:
        names = ", ".join(s.c_function_name for s in riscv_only)
        raise RuntimeError(
            f"Cannot build for host: kernel(s) [{names}] are marked "
            f"'host_compatible: false' (RISC-V / RVV only). "
            f"Use 'python build.py --araxl' instead, or change the kernel "
            f"in kernels.json to a portable C implementation."
        )

    target = tvm.target.Target("llvm")
    ex = tvm.compile(mod, target)

    dump_codegen(ex, out_dir, "03_codegen_host")

    srcs, incs = _resolve_c_inputs(specs)
    cflags = ["-O2", "-fPIC"] + [f"-I{d}" for d in incs]
    so_path = out_dir / "model_with_extern.so"

    ex.export_library(
        str(so_path),
        fcompile=make_fcompile(srcs, extra_cflags=cflags),
    )
    print(f"  -> {so_path}")
    return so_path


def build_araxl_ll(mod: tvm.IRModule, out_dir: Path, app_name: str) -> Path:
    """Emit LLVM IR for the AraXL RISC-V flow (matches tvm-apps/Makefile)."""
    out_dir.mkdir(parents=True, exist_ok=True)

    target = tvm.target.Target({
        "kind": "llvm",
        "mtriple": "riscv64-unknown-elf",
        "mattr": ["+v", "+m", "+f", "+d"],
        "mabi": "lp64d",
    })

    with tvm.transform.PassContext(opt_level=3):
        ex = tvm.compile(mod, target)

    llvm_mod = ex.mod.imports[0] if len(ex.mod.imports) else ex.mod
    ll_path = out_dir / f"{app_name}.ll"
    s_path = out_dir / f"{app_name}.s"
    ll_path.write_text(llvm_mod.inspect_source("ll"), encoding="utf-8")
    s_path.write_text(llvm_mod.inspect_source("asm"), encoding="utf-8")
    print(f"  -> {ll_path}")
    print(f"  -> {s_path}")
    return ll_path


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", default=str(DEFAULT_JSON))
    p.add_argument("--araxl", action="store_true",
                   help="Emit LLVM IR for AraXL/RISC-V instead of a host .so")
    p.add_argument("--app", default="model_with_extern",
                   help="App name (used for the emitted .ll filename)")
    p.add_argument("--out", default=str(HERE / "build"))
    args = p.parse_args(argv)

    specs = load_kernels(args.json)
    print(f"Loaded {len(specs)} custom kernel(s) from {args.json}")
    for s in specs:
        print(f"  - {s.relax_op} -> {s.c_function_name} (src: {s.source_file})")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n[1/4] Building Relax model from Conv2DOnly ...")
    mod = build_relax_model()
    dump_ir(mod, out_dir / "00_exported_relax.py")

    print("\n[2/4] Running custom extern-kernel pass ...")
    mod = replace_with_extern_kernels(specs)(mod)
    dump_ir(mod, out_dir / "01_after_extern_pass_relax_tir.py")

    print("\n[3/4] Running Relax 'zero' lowering pipeline ...")
    mod = relax.get_pipeline("zero")(mod)
    dump_ir(mod, out_dir / "02_zero_pipeline_relax_tir.py")

    print("\n[4/4] Codegen ...")
    if args.araxl:
        ll = build_araxl_ll(mod, out_dir, args.app)
        print(f"\nWrote {ll}")
        print("Next: feed this .ll plus the C sources in kernels.json into")
        print("tvm-apps/Makefile (override TVM_OBJ deps to include the C objects).")
    else:
        so = build_host(mod, specs, out_dir)
        print(f"\nWrote {so}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
