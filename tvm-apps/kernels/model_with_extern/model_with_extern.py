"""Generator for model_with_extern: a single fmatmul32 extern-kernel TIR wrapper.

Builds an IRModule with one PrimFunc (extern_fmatmul32_0) that forwards to the
hand-written fmatmul32 C kernel from AraXL/apps/fmatmul/kernel/fmatmul32.c.

Shape: (1, 784) x (784, 256) -> (1, 256) matching model_with_extern_main.c.

Stage outputs
-------------
build/model_with_extern/00_codegen/ir/
  00_tir.py      TIR PrimFunc text before codegen
  03_codegen.ll  final LLVM IR
  03_codegen.s   final ASM

Build input (Makefile LL_FILE)
------------------------------
build/model_with_extern/00_codegen/final/model_with_extern.ll
build/model_with_extern/00_codegen/final/model_with_extern.s
"""
import os
from pathlib import Path

import tvm
from tvm import ir

from ..common.common import target, save_kernel

_HERE = Path(__file__).resolve()
_TVM_APPS = _HERE.parent.parent.parent          # tvm-apps/

import sys as _sys
if str(_TVM_APPS) not in _sys.path:
    _sys.path.insert(0, str(_TVM_APPS))

from pipeline import load_catalog, make_extern_primfunc  # noqa: E402

KERNELS_JSON = _TVM_APPS / "pipeline" / "kernels.json"
APP = "model_with_extern"
OUTPUT_IR_DIR = Path(os.environ.get("ARAXL_APP_IR_DIR", _TVM_APPS / "build" / APP / "00_codegen" / "ir"))


if __name__ == "__main__":
    catalog = load_catalog(KERNELS_JSON)
    kernel = catalog.kernels["fmatmul32"]

    # Build TIR wrapper: (1,784) x (784,256) -> (1,256)
    pf = make_extern_primfunc(
        kernel,
        input_shapes=[[1, 784], [784, 256]],
        output_shape=[1, 256],
        func_symbol="extern_fmatmul32_0",
    )

    mod = ir.IRModule({"extern_fmatmul32_0": pf})

    print(f"\n[1/2] TIR PrimFunc:")
    print(f"\n[2/2] Codegen to LLVM IR ...")
    with tvm.transform.PassContext(opt_level=0):
        lib = tvm.build(mod, target=target)

    save_kernel(APP, lib, source_mod=mod, ir_dir=OUTPUT_IR_DIR)
    print(f"\nDone. Run: make compile app={APP} && make sim app={APP}")
