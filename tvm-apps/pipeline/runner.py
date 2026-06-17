"""Pipeline runner: model definition -> LLVM IR for AraXL.

Invoked by the Makefile ``tvm-ir`` target for model apps::

    python -m pipeline.runner --app quick_start

Flow:

  1. Import ``models/<app>/<app>.py`` and call ``get_model()`` +
     ``get_export_spec()`` (or ``build_relax_model()`` for models that
     prefer to handle export themselves).
  2. Load ``pipeline/kernels.json``.
  3. Run :func:`inject_custom_kernels` to rewrite matched Relax ops to
     ``R.call_tir`` / ``T.call_extern`` wrappers.
  4. Lower with ``relax.get_pipeline("zero")``.
  5. Codegen to LLVM IR for riscv64-unknown-elf.
  6. Write stage dumps to ``build/<app>/00_codegen/ir/`` and final
     ``.ll``/``.s`` to ``build/<app>/00_codegen/final/`` (Makefile ``LL_FILE``).
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path
from typing import List

import tvm
from tvm import relax
from tvm.relax.frontend import nn

_HERE = Path(__file__).resolve().parent
_TVM_APPS = _HERE.parent

KERNELS_JSON = _HERE / "kernels.json"

_RISCV_TARGET = tvm.target.Target({
    "kind": "llvm",
    "mtriple": "riscv64-unknown-elf",
    "mattr": ["+v", "+m", "+f", "+d"],
    "mabi": "lp64d",
    "opt-level": 0,
})


def _load_model_module(app: str):
    path = _TVM_APPS / "models" / app / f"{app}.py"
    if not path.exists():
        raise FileNotFoundError(f"No model found at {path}")
    spec = importlib.util.spec_from_file_location(f"models.{app}.{app}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load model module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod   # TVMScript's inspect.getfile needs this
    sys.path.insert(0, str(_TVM_APPS))
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    finally:
        if sys.path and sys.path[0] == str(_TVM_APPS):
            sys.path.pop(0)
    return mod


def _build_relax_mod(app: str) -> tvm.IRModule:
    m = _load_model_module(app)
    if hasattr(m, "build_relax_model"):
        result = m.build_relax_model()
        if not isinstance(result, tvm.IRModule):
            raise TypeError(f"build_relax_model() must return tvm.IRModule, got {type(result)!r}")
        return result
    if hasattr(m, "get_model") and hasattr(m, "get_export_spec"):
        model = m.get_model()
        spec = m.get_export_spec()
        irmod, _params = model.export_tvm(spec=spec)
        return irmod
    raise RuntimeError(
        f"models/{app}/{app}.py must define either build_relax_model() "
        f"or get_model() + get_export_spec()."
    )


def _default_ir_dir(app: str) -> Path:
    return Path(os.environ.get("ARAXL_APP_IR_DIR", _TVM_APPS / "build" / app / "00_codegen" / "ir"))


def _default_tvm_dir(app: str) -> Path:
    return Path(os.environ.get("ARAXL_APP_TVM_DIR", _TVM_APPS / "build" / app / "00_codegen" / "final"))


def run(app: str, ir_dir: Path | None = None, tvm_dir: Path | None = None) -> int:
    from . import dump_text, load_catalog
    from .dpl_pass import inject_custom_kernels

    ir_dir = ir_dir or _default_ir_dir(app)
    tvm_dir = tvm_dir or _default_tvm_dir(app)

    catalog = load_catalog(KERNELS_JSON)
    print(f"Loaded {len(catalog.kernels)} kernel(s) and {len(catalog.rules)} rule(s).")

    print(f"\n[1/4] Exporting Relax model for '{app}' ...")
    mod = _build_relax_mod(app)
    dump_text(mod.script(), ir_dir / "00_exported_relax.py")

    print("\n[2/4] Injecting extern kernels ...")
    mod = inject_custom_kernels(catalog)(mod)
    dump_text(mod.script(), ir_dir / "01_after_dpl_pass.py")

    print("\n[3/4] Running Relax zero pipeline (FuseTIR) ...")
    mod = relax.get_pipeline("zero")(mod)
    dump_text(mod.script(), ir_dir / "02_zero_pipeline.py")

    print("\n[4/4] Codegen to LLVM IR ...")
    with tvm.transform.PassContext(opt_level=3):
        ex = tvm.compile(mod, _RISCV_TARGET)

    llvm_mod = ex.mod.imports[0] if len(ex.mod.imports) else ex.mod
    ll_text = llvm_mod.inspect_source("ll")
    asm_text = llvm_mod.inspect_source("asm")

    dump_text(ll_text, ir_dir / "03_codegen.ll")
    dump_text(asm_text, ir_dir / "03_codegen.s")

    tvm_dir.mkdir(parents=True, exist_ok=True)
    (tvm_dir / f"{app}.ll").write_text(ll_text, encoding="utf-8")
    (tvm_dir / f"{app}.s").write_text(asm_text, encoding="utf-8")
    print(f"  -> {tvm_dir / f'{app}.ll'}")
    print(f"  -> {tvm_dir / f'{app}.s'}")

    return 0


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description="AraXL pipeline runner")
    p.add_argument("--app", required=True, help="App name (e.g. quick_start)")
    p.add_argument("--ir-dir", type=Path, default=None, help="Directory for staged IR dumps")
    p.add_argument("--tvm-dir", type=Path, default=None, help="Directory for final LLVM/ASM")
    args = p.parse_args(argv)
    return run(args.app, args.ir_dir, args.tvm_dir)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
