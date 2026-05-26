from tvm.script import ir as I # Module level decorator
from tvm.script import tirx as T # Tensor primitives 
import tvm # Main package for build, target, transfor
from ..common.common import target, save_kernel


@I.ir_module # Tells TVM to treat class as a tvm ir module
class DotProduct:
    @T.prim_func # Mark this as a primitive function that TVM will compile
    def main(a: T.Buffer((64,), "float32"),
             b: T.Buffer((64,), "float32"),
             c: T.Buffer((1,), "float32")):
        T.func_attr({"global_symbol": "dotproduct", "tirx.noalias": True})
        for i in range(64):
            with T.sblock("dotproduct"):
                vi = T.axis.reduce(64, i)
                with T.init():
                    c[0] = T.float32(0)
                c[0] = c[0] + a[vi] * b[vi]


if __name__ == "__main__":
    with tvm.transform.PassContext(opt_level=3):
        lib = tvm.build(DotProduct, target=target)
    save_kernel("dotproduct", lib, source_mod=DotProduct)