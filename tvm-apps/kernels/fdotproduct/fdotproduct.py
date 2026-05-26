from tvm.script import ir as I
from tvm.script import tirx as T
import tvm

from ..common.common import target, save_kernel


@I.ir_module
class FDotProduct:
    @T.prim_func
    def main(a: T.Buffer((64,), "float32"),
             b: T.Buffer((64,), "float32"), 
             c: T.Buffer((1,), "float32")):
        T.func_attr({"global_symbol": "fdotproduct", "tirx.noalias": True})
        c[0] = T.call_extern("float32", "fdotp_v32b", a.data, b.data, T.cast(64, "uint64"))


if __name__ == "__main__":
    with tvm.transform.PassContext(opt_level=3):
        lib = tvm.build(FDotProduct, target=target)
    save_kernel("fdotproduct", lib, source_mod=FDotProduct)