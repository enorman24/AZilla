"""TIR PrimFunc synthesis for extern-kernel wrappers.

``make_extern_primfunc`` builds a TIR PrimFunc that forwards buffer args
(and optional scalars / shape vars) to a hand-written C kernel via
``T.call_extern``.  Used by the DPL injection pass and directly by
``kernels/model_with_extern/model_with_extern.py``.
"""

from __future__ import annotations

from typing import Dict, List, Sequence

from tvm import ir, relax
from tvm import tirx as tir

from .kernels_config import BufferRef, KernelDef, ScalarLiteral, ShapeVarRef


def _resolve_shape_var(
    kernel: KernelDef,
    var_name: str,
    input_shapes: Sequence[Sequence[int]],
    output_shape: Sequence[int],
) -> int:
    """Look up a ``shape_var`` in the kernel's ``shape_bindings``."""
    if var_name not in kernel.shape_bindings:
        raise ValueError(
            f"kernel '{kernel.name}': arg_layout uses shape_var '{var_name}' "
            f"but no shape_bindings entry exists for it."
        )
    buf_name, axis = kernel.shape_bindings[var_name]
    if buf_name == "out":
        shape = output_shape
    elif buf_name.startswith("in"):
        idx = int(buf_name[2:])
        if idx >= len(input_shapes):
            raise ValueError(
                f"kernel '{kernel.name}': shape_bindings['{var_name}'] refers "
                f"to '{buf_name}' but only {len(input_shapes)} inputs provided."
            )
        shape = input_shapes[idx]
    else:
        raise ValueError(
            f"kernel '{kernel.name}': shape_bindings['{var_name}'] has unknown "
            f"buffer '{buf_name}' (expected 'in0', 'in1', ..., 'out')."
        )
    if axis < 0 or axis >= len(shape):
        raise ValueError(
            f"kernel '{kernel.name}': shape_bindings['{var_name}'] axis "
            f"{axis} out of range for shape {list(shape)}."
        )
    return int(shape[axis])


def _scalar_imm(dtype: str, value: float) -> tir.PrimExpr:
    if dtype.startswith("int") or dtype.startswith("uint"):
        return tir.IntImm(dtype, int(value))
    if dtype.startswith("float"):
        return tir.FloatImm(dtype, float(value))
    raise ValueError(f"Unsupported scalar dtype '{dtype}'")


def _shape_int64(dims: Sequence[int]) -> List[tir.PrimExpr]:
    """Build a buffer shape with int64 dims.

    Required for structural equality with buffers TVM auto-generates
    elsewhere (Relax struct_info, lowered ``transpose`` PrimFuncs, etc.,
    all use ``T.int64`` extents). Mixing int32 and int64 dims triggers
    ``Inconsistent buffers ... mapped to the same relax var`` during
    lowering of ``R.call_tir``.
    """
    return [tir.IntImm("int64", int(d)) for d in dims]


def make_extern_primfunc(
    kernel: KernelDef,
    input_shapes: List[List[int]],
    output_shape: List[int],
    func_symbol: str,
) -> tir.PrimFunc:
    """Build a TIR PrimFunc that forwards args to the kernel's C function."""
    dtypes = kernel.buffer_dtypes
    num_inputs = kernel.num_inputs

    if len(input_shapes) != num_inputs:
        raise ValueError(
            f"{kernel.c_function_name}: expected {num_inputs} input shapes, "
            f"got {len(input_shapes)}"
        )

    all_shapes = list(input_shapes) + [list(output_shape)]
    if len(all_shapes) != len(dtypes):
        raise ValueError(
            f"{kernel.c_function_name}: shapes/dtypes length mismatch "
            f"({len(all_shapes)} vs {len(dtypes)})"
        )

    handles: List[tir.Var] = []
    buffer_map: Dict[tir.Var, tir.Buffer] = {}
    buffers_by_name: Dict[str, tir.Buffer] = {}

    for i, (shape, dtype) in enumerate(zip(all_shapes, dtypes)):
        name = "out" if i == num_inputs else f"in{i}"
        h = tir.Var(f"{name}_handle", "handle")
        buf = tir.decl_buffer(_shape_int64(shape), dtype=dtype, name=name)
        handles.append(h)
        buffer_map[h] = buf
        buffers_by_name[name] = buf

    call_args: List[tir.PrimExpr] = []
    for item in kernel.effective_arg_layout():
        if isinstance(item, BufferRef):
            if item.name not in buffers_by_name:
                raise ValueError(
                    f"{kernel.c_function_name}: arg_layout references unknown "
                    f"buffer '{item.name}'. Known: {sorted(buffers_by_name)}"
                )
            call_args.append(buffers_by_name[item.name].data)
        elif isinstance(item, ScalarLiteral):
            call_args.append(_scalar_imm(item.dtype, item.value))
        elif isinstance(item, ShapeVarRef):
            dim = _resolve_shape_var(kernel, item.name, input_shapes, output_shape)
            call_args.append(_scalar_imm(item.dtype, dim))
        else:
            raise TypeError(f"Unknown arg_layout item: {item!r}")

    # FuseTIR expects schedulable PrimFuncs (root SBlockRealize body).
    extern_eval = tir.Evaluate(
        tir.call_extern("int32", kernel.c_function_name, *call_args)
    )
    root_block = tir.SBlock(
        iter_vars=[],
        reads=[],
        writes=[],
        name_hint="root",
        body=extern_eval,
    )
    body = tir.SBlockRealize(
        iter_values=[],
        predicate=True,
        block=root_block,
    )

    pf = tir.PrimFunc(params=handles, body=body, buffer_map=buffer_map)
    pf = pf.with_attr("global_symbol", func_symbol)
    pf = pf.with_attr("tir.noalias", True)
    return pf
