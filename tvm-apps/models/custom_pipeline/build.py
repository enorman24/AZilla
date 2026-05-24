"""End-to-end build entry point for the custom kernel pipeline.

Flow:

    1. Define / import a Relax model (here: the quick_start MLP).
    2. Load ``kernels.json`` -> :class:`KernelCatalog`
       (kernels catalog + matching rules; model-agnostic).
    3. Run :func:`inject_custom_kernels_tracked` to rewrite matched
       Relax ops into ``call_tir`` / ``call_extern`` invocations.
       Only kernels actually selected by the rule engine are returned
       for downstream linking.
    4. Lower with the standard ``relax.get_pipeline("zero")``.
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
import importlib.util
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from kernels_config import KernelCatalog, KernelDef, load_catalog  # type: ignore
    from custom_pass import inject_custom_kernels_tracked  # type: ignore
else:
    from .kernels_config import KernelCatalog, KernelDef, load_catalog
    from .custom_pass import inject_custom_kernels_tracked

import tvm
from tvm import relax
from tvm.relax.frontend import nn


HERE = Path(__file__).resolve().parent
TVM_APPS_DIR = HERE.parent.parent
ARA_DIR = TVM_APPS_DIR.parent
DEFAULT_JSON = HERE / "kernels.json"


# ----------------------------------------------------------------------
# Quick-start MLP model (matches tvm-apps/models/quick_start.py)
# ----------------------------------------------------------------------

class MLPModel(nn.Module):
    """Two-layer MLP from the TVM quick_start tutorial.

    Forward graph (after ``export_tvm``) contains two ``relax.matmul``
    callsites with different shapes:

      * fc1: ``(1, 784)  x (784, 256) -> (1, 256)``
      * fc2: ``(1, 256)  x (256, 10)  -> (1, 10)``

    Both are matched by the ``matmul_fp32_2d`` rule in ``kernels.json``
    and routed to the single ``fmatmul32`` C kernel; per-callsite
    wrappers carry the right ``M, N, P`` scalars.
    """

    # def __init__(self):
    #     super().__init__()
    #     self.fc1 = nn.Linear(784, 256)
    #     self.relu1 = nn.ReLU()
    #     self.fc2 = nn.Linear(256, 10)

    # def forward(self, x):
    #     x = self.fc1(x)
    #     x = self.relu1(x)
    #     x = self.fc2(x)
    #     return x


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
    # mod, _params = MLPModel().export_tvm(
    #     spec={"forward": {"x": nn.spec.Tensor((1, 784), "float32")}}
    # )

    mod, _params = MLPModel().export_tvm(
        spec={"forward": {"x": nn.spec.Tensor((1, 1, 18, 18), "float64")}}
    )
    return mod


def _load_user_model_module(model_path: str):
    """Dynamically import a user model module from ``--model`` path."""
    path = Path(model_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"--model path does not exist: {path}")

    spec = importlib.util.spec_from_file_location("custom_pipeline_user_model", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import model module from: {path}")

    module = importlib.util.module_from_spec(spec)

    # Allow relative imports from the model's directory.
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        # Remove only if it is still our inserted head.
        if sys.path and sys.path[0] == str(path.parent):
            sys.path.pop(0)

    return module, path


def build_relax_model_from_path(model_path: str) -> Tuple[tvm.IRModule, str]:
    """Build IRModule from an external model file.

    Supported contracts in ``model.py``:

      1. ``build_relax_model() -> tvm.IRModule``
      2. ``get_model()`` + ``get_export_spec()`` where:
         ``get_model()`` returns an ``nn.Module`` and
         ``get_export_spec()`` returns ``export_tvm(spec=...)`` input.
    """
    module, resolved_path = _load_user_model_module(model_path)

    if hasattr(module, "build_relax_model"):
        mod = module.build_relax_model()
        if not isinstance(mod, tvm.IRModule):
            raise TypeError(
                f"{resolved_path}: build_relax_model() must return tvm.IRModule, "
                f"got {type(mod)!r}"
            )
        return mod, str(resolved_path)

    has_factory = hasattr(module, "get_model")
    has_spec = hasattr(module, "get_export_spec")
    if has_factory and has_spec:
        model = module.get_model()
        export_spec = module.get_export_spec()
        mod, _params = model.export_tvm(spec=export_spec)
        return mod, str(resolved_path)

    raise RuntimeError(
        f"{resolved_path}: expected either build_relax_model(), or both "
        f"get_model() and get_export_spec()."
    )
    


# ----------------------------------------------------------------------
# Codegen helpers
# ----------------------------------------------------------------------

def make_fcompile(extra_sources: Iterable[str], extra_cflags: List[str] | None = None):
    """Return an ``fcompile`` callable for ``export_library``.

    It compiles & links the TVM-generated object together with the
    handwritten C files from the kernels actually selected by the pass.
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


def _resolve_c_inputs(used: List[KernelDef]) -> tuple[List[str], List[str]]:
    """Resolve all .c source files and ``-I`` include dirs.

    Paths in ``kernels.json`` are interpreted relative to the AraXL
    repo root (``ARA_DIR``).
    """
    srcs: List[str] = []
    incs: List[str] = []
    for k in used:
        for f in [k.source_file, *k.extra_sources]:
            srcs.append(str((ARA_DIR / f).resolve()))
        for d in k.include_dirs:
            incs.append(str((ARA_DIR / d).resolve()))
    return srcs, incs


# ----------------------------------------------------------------------
# Build flavors
# ----------------------------------------------------------------------

def build_host(mod: tvm.IRModule, used: List[KernelDef], out_dir: Path) -> Path:
    """Build a host-side shared library that links the custom C kernels.

    Kernels marked ``host_compatible: false`` (RVV intrinsics, RISC-V
    asm) cannot run on a host x86 build; we reject them with a clear
    message and recommend ``--araxl``.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    riscv_only = [k for k in used if not k.host_compatible]
    if riscv_only:
        names = ", ".join(k.c_function_name for k in riscv_only)
        raise RuntimeError(
            f"Cannot build for host: kernel(s) [{names}] are marked "
            f"'host_compatible: false' (RISC-V / RVV only). "
            f"Use 'python build.py --araxl' instead, or change the kernel "
            f"in kernels.json to a portable C implementation."
        )

    target = tvm.target.Target("llvm")
    ex = tvm.compile(mod, target)

    dump_codegen(ex, out_dir, "03_codegen_host")

    srcs, incs = _resolve_c_inputs(used)
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


# ----------------------------------------------------------------------
# Pipeline driver
# ----------------------------------------------------------------------

def _print_catalog(catalog: KernelCatalog, json_path: str) -> None:
    print(f"Loaded {len(catalog.kernels)} kernel(s) and "
          f"{len(catalog.rules)} rule(s) from {json_path}")
    for k in catalog.kernels.values():
        host_tag = "host-ok" if k.host_compatible else "riscv-only"
        print(f"  kernel  {k.name}: {k.c_function_name} [{host_tag}] "
              f"(src={k.source_file})")
    for r in catalog.rules_sorted():
        ops = ",".join(r.match.relax_ops)
        print(f"  rule    {r.name}@{r.priority}: [{ops}] -> {r.kernel}")


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", default=str(DEFAULT_JSON))
    p.add_argument(
        "--model",
        default=None,
        help=(
            "Path to a model.py file. Supported APIs: "
            "build_relax_model() OR get_model()+get_export_spec()."
        ),
    )
    p.add_argument("--araxl", action="store_true",
                   help="Emit LLVM IR for AraXL/RISC-V instead of a host .so")
    p.add_argument("--app", default="model_with_extern",
                   help="App name (used for the emitted .ll filename)")
    p.add_argument("--out", default=str(HERE / "build"))
    args = p.parse_args(argv)

    catalog = load_catalog(args.json)
    _print_catalog(catalog, args.json)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.model:
        print(f"\n[1/4] Building Relax model from {args.model} ...")
        mod, model_desc = build_relax_model_from_path(args.model)
    else:
        print("\n[1/4] Building Relax model from built-in default model ...")
        mod = build_relax_model()
        model_desc = "built-in default model"
    print(f"  model source: {model_desc}")
    dump_ir(mod, out_dir / "00_exported_relax.py")

    print("\n[2/4] Running custom extern-kernel pass ...")
    pass_, used = inject_custom_kernels_tracked(catalog)
    mod = pass_(mod)
    dump_ir(mod, out_dir / "01_after_extern_pass_relax_tir.py")

    if used:
        print(f"  selected {len(used)} kernel(s):")
        for k in used:
            print(f"    - {k.name} -> {k.c_function_name} ({k.source_file})")
    else:
        print("  no Relax callsites matched any rule; module unchanged.")

    print("\n[3/4] Running Relax 'zero' lowering pipeline ...")
    mod = relax.get_pipeline("zero")(mod)
    dump_ir(mod, out_dir / "02_zero_pipeline_relax_tir.py")

    print("\n[4/4] Codegen ...")
    if args.araxl:
        ll = build_araxl_ll(mod, out_dir, args.app)
        print(f"\nWrote {ll}")
        print("Next: feed this .ll plus the C sources from the selected")
        print("kernels into tvm-apps/Makefile (override TVM_OBJ deps to")
        print("include the C objects).")
    else:
        so = build_host(mod, used, out_dir)
        print(f"\nWrote {so}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
