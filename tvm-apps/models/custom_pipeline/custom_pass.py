"""Custom Relax pass that swaps native Relax ops for external C kernels.

Pipeline of a matched op:

    Relax R.Call(<op>, [x, w, ...])
        ->  R.call_tir(extern_<c_fn>, [x, w, ...], out_sinfo=...)
              |
              v
        TIR PrimFunc extern_<c_fn>(handle, handle, ..., handle):
            with T.match_buffer for each arg,
            T.call_extern("int32", "<c_fn>", buf_in0.data, buf_in1.data, ...,
                          buf_out.data)

Buffer-pointer flow:

  - In Relax, each arg is a Tensor; its data lives in a DLTensor.
  - ``R.call_tir`` packs those tensors into TIR handles and invokes the
    PrimFunc.
  - Inside the PrimFunc, ``T.match_buffer`` (here built via ``decl_buffer``
    + ``buffer_map``) gives us a Buffer whose ``.data`` is a raw pointer
    (TIR ``Var`` of type ``handle``).
  - ``T.call_extern`` forwards those raw pointers, in C-ABI order, to the
    handwritten C function. The C function therefore sees plain
    ``float*`` arguments and can operate on the underlying memory.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import sys
from pathlib import Path

import tvm
from tvm import ir, relax
from tvm import tirx as tir
from tvm.relax.expr import _update_struct_info
from tvm.relax.expr_functor import PyExprMutator, mutator

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from kernels_config import (  # type: ignore
        BufferRef, KernelSpec, ScalarLiteral, specs_by_op,
    )
else:
    from .kernels_config import (
        BufferRef, KernelSpec, ScalarLiteral, specs_by_op,
    )


def _shape_to_int_list(shape) -> List[int]:
    """Best-effort conversion of a Relax/TIR shape to a Python list[int]."""
    out: List[int] = []
    for dim in shape:
        if isinstance(dim, tir.IntImm):
            out.append(int(dim.value))
        elif isinstance(dim, int):
            out.append(dim)
        else:
            raise ValueError(
                f"Custom kernel pass needs static shapes, got non-int dim: {dim!r}"
            )
    return out


def make_extern_primfunc(
    spec: KernelSpec,
    input_shapes: List[List[int]],
    output_shape: List[int],
    func_symbol: str,
) -> tir.PrimFunc:
    """Build a TIR PrimFunc that forwards args to ``spec.c_function_name``.

    PrimFunc signature: one ``handle`` per buffer in TVM call order
    (inputs first, then output). ``buffer_map`` ties each handle to a
    typed ``tir.Buffer`` so ``buf.data`` is a raw C-ABI pointer.

    The ``T.call_extern`` arg list, in contrast, is built from
    ``spec.effective_arg_layout()`` so the C function sees its args in
    its own native order (e.g. fconv2d_3x3 wants ``(o, i, f, R, C, F)``)
    and can include scalar literals after the buffer pointers.
    """
    dtypes = spec.buffer_dtypes
    num_inputs = spec.num_inputs

    if len(input_shapes) != num_inputs:
        raise ValueError(
            f"{spec.c_function_name}: expected {num_inputs} input shapes, "
            f"got {len(input_shapes)}"
        )

    all_shapes = list(input_shapes) + [list(output_shape)]
    assert len(all_shapes) == len(dtypes), (
        f"{spec.c_function_name}: shapes/dtypes length mismatch "
        f"({len(all_shapes)} vs {len(dtypes)})"
    )

    handles: List[tir.Var] = []
    buffer_map: Dict[tir.Var, tir.Buffer] = {}
    buffers_by_name: Dict[str, tir.Buffer] = {}

    for i, (shape, dtype) in enumerate(zip(all_shapes, dtypes)):
        name = "out" if i == num_inputs else f"in{i}"
        h = tir.Var(f"{name}_handle", "handle")
        buf = tir.decl_buffer(shape, dtype=dtype, name=name)
        handles.append(h)
        buffer_map[h] = buf
        buffers_by_name[name] = buf

    call_args = []
    for item in spec.effective_arg_layout():
        if isinstance(item, BufferRef):
            if item.name not in buffers_by_name:
                raise ValueError(
                    f"{spec.c_function_name}: arg_layout references unknown "
                    f"buffer '{item.name}'. Known: {sorted(buffers_by_name)}"
                )
            call_args.append(buffers_by_name[item.name].data)
        elif isinstance(item, ScalarLiteral):
            if item.dtype.startswith("int"):
                call_args.append(tir.IntImm(item.dtype, int(item.value)))
            elif item.dtype.startswith("float"):
                call_args.append(tir.FloatImm(item.dtype, float(item.value)))
            else:
                raise ValueError(
                    f"{spec.c_function_name}: unsupported scalar dtype '{item.dtype}'"
                )
        else:
            raise TypeError(f"Unknown arg_layout item: {item!r}")

    body = tir.Evaluate(
        tir.call_extern("int32", spec.c_function_name, *call_args)
    )

    pf = tir.PrimFunc(params=handles, body=body, buffer_map=buffer_map)
    pf = pf.with_attr("global_symbol", func_symbol)
    pf = pf.with_attr("tir.noalias", True)
    return pf


@mutator
class ReplaceWithExternCallMutator(PyExprMutator):
    """Walks Relax functions and rewrites matching ops to ``call_tir``.

    For each matched ``Call``:
      1) compute input shapes from arg ``struct_info``,
      2) build (and cache) the TIR PrimFunc wrapping ``call_extern``,
      3) register it in the module under a fresh GlobalVar,
      4) emit ``R.call_tir(gv, args, out_sinfo)``.
    """

    def __init__(self, mod: ir.IRModule, specs: Dict[str, KernelSpec]):
        super().__init__(mod)
        self._mod = mod
        self._specs = specs
        self._cache: Dict[Tuple, ir.GlobalVar] = {}

    def visit_call_(self, call: relax.Call) -> relax.Expr:  # noqa: D401
        call = super().visit_call_(call)

        op = call.op
        if not isinstance(op, ir.Op) or op.name not in self._specs:
            return call

        spec = self._specs[op.name]

        input_shapes: List[List[int]] = []
        for arg in call.args:
            sinfo = arg.struct_info
            if not isinstance(sinfo, relax.TensorStructInfo):
                return call
            input_shapes.append(_shape_to_int_list(sinfo.shape))

        if len(input_shapes) != spec.num_inputs:
            return call

        cache_key = (
            spec.c_function_name,
            tuple(tuple(s) for s in input_shapes),
            tuple(spec.target_shape),
        )

        if cache_key not in self._cache:
            func_symbol = f"extern_{spec.c_function_name}"
            pf = make_extern_primfunc(
                spec, input_shapes, spec.target_shape, func_symbol
            )
            gv = ir.GlobalVar(func_symbol)
            _update_struct_info(gv, relax.FuncStructInfo.opaque_func())
            self._mod[gv] = pf
            self._cache[cache_key] = gv

        gv = self._cache[cache_key]
        out_sinfo = relax.TensorStructInfo(
            tuple(spec.target_shape), spec.output_dtype
        )
        return relax.call_tir(gv, list(call.args), out_sinfo=out_sinfo)


def replace_with_extern_kernels(specs: List[KernelSpec]):
    """Factory returning a module pass parameterized by the kernel registry.

    Use as::

        mod = replace_with_extern_kernels(specs)(mod)

    The pass mutates a copy of ``mod``: it inserts one TIR PrimFunc per
    unique (c_function, input_shapes) tuple and rewrites Relax callsites
    to point at it.
    """
    indexed = specs_by_op(specs)

    @ir.transform.module_pass(opt_level=0, name="ReplaceWithExternKernels")
    def _pass(mod: ir.IRModule, _ctx) -> ir.IRModule:
        new_mod = ir.IRModule(
            {gv: func for gv, func in mod.functions.items()},
            attrs=mod.attrs,
        )

        mutator_inst = ReplaceWithExternCallMutator(new_mod, indexed)

        for gv, func in list(new_mod.functions.items()):
            if isinstance(func, relax.Function):
                new_mod[gv] = mutator_inst.visit_expr(func)

        return new_mod

    return _pass
