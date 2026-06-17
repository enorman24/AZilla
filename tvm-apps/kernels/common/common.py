import os
import sys
from pathlib import Path

import tvm


TVM_APPS_DIR = Path(__file__).resolve().parents[2]

if str(TVM_APPS_DIR) not in sys.path:
    sys.path.insert(0, str(TVM_APPS_DIR))

try:
    from pipeline import dump_text as _dump_text
except ImportError:
    def _dump_text(text: str, path) -> None:  # type: ignore[misc]
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print(f"  -> {p}")


target = tvm.target.Target({
    "kind": "llvm", # llvm backend
    "mtriple": "riscv64-unknown-elf", # Target / what representation to bring it down to
    "mattr": ["+v", "+m", "+f", "+d"], # vector extension, mult/div, single-precision float, double-precision float
    "mabi": "lp64d", # depends on the araxl toolchain -> May be changed
    "opt-level": 0  # let riscv-llvm 20 optimize; prevents LLVM 22 scalable vectorization
})


def save_kernel(
    name: str,
    lib,
    tvm_dir: str | os.PathLike[str] | None = None,
    source_mod=None,
    ir_dir: str | os.PathLike[str] | None = None,
):
    output_dir = Path(
        tvm_dir
        or os.environ.get("ARAXL_APP_TVM_DIR")
        or TVM_APPS_DIR / "build" / name / "00_codegen" / "final"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    if source_mod is not None:
        ir_out = Path(
            ir_dir
            or os.environ.get("ARAXL_APP_IR_DIR")
            or TVM_APPS_DIR / "build" / name / "00_codegen" / "ir"
        )
        ir_out.mkdir(parents=True, exist_ok=True)
        _dump_text(source_mod.script(), ir_out / "00_tir.py")
        _dump_text(lib.inspect_source("ll"), ir_out / "03_codegen.ll")
        _dump_text(lib.inspect_source("asm"), ir_out / "03_codegen.s")

    with open(output_dir / f"{name}.s", "w") as f:
        f.write(lib.inspect_source("asm"))

    with open(output_dir / f"{name}.ll", "w") as f:
        f.write(lib.inspect_source("ll"))
