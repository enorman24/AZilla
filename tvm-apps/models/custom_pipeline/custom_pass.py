"""Custom Relax pass that rewrites matched ops to external C kernels.

Pipeline timing:

    Relax model (post ``export_tvm``)
        |
        v
    [InjectCustomKernels]   <-- this pass
        |
        v
    relax.get_pipeline("zero")   <-- TVM standard lowering continues

For each Relax ``Call``:

  1. Build a :class:`CallSiteInfo` from the call's ``struct_info``.
  2. Run the rule engine (``select_rule``) against the JSON catalog.
  3. If a rule matches, synthesize a TIR ``PrimFunc`` whose body is
     ``T.call_extern("int32", c_function_name, *args)`` where ``args``
     are assembled from the kernel's ``arg_layout``:
        - buffer entries  -> ``Buffer.data`` (raw C pointer)
        - scalar entries  -> compile-time literal
        - shape_var       -> resolved per callsite from the input shapes
  4. Register that PrimFunc as a fresh GlobalVar in the IRModule.
  5. Replace the original ``Call`` with ``R.call_tir(gv, args, out_sinfo)``
     where ``out_sinfo`` follows the rule's output policy
     (literal shape OR named inference, e.g. ``infer_matmul_2d``).

The pass is fully data-driven from ``kernels.json``; nothing model
specific is hardcoded here.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import tvm
from tvm import ir, relax
from tvm import tirx as tir
from tvm.relax.expr import _update_struct_info
from tvm.relax.expr_functor import PyExprMutator, mutator

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from kernels_config import (  # type: ignore
        BufferRef,
        CallSiteInfo,
        KernelCatalog,
        KernelDef,
        KernelRule,
        ScalarLiteral,
        ShapeVarRef,
        resolve_output_shape,
        select_rule,
    )
else:
    from .kernels_config import (
        BufferRef,
        CallSiteInfo,
        KernelCatalog,
        KernelDef,
        KernelRule,
        ScalarLiteral,
        ShapeVarRef,
        resolve_output_shape,
        select_rule,
    )


# ----------------------------------------------------------------------
# Shape extraction
# ----------------------------------------------------------------------

def _shape_to_int_list(shape) -> List[int]:
    """Best-effort conversion of a Relax/TIR shape to a Python ``list[int]``."""
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


def _extract_callsite_info(call: relax.Call) -> CallSiteInfo | None:
    op = call.op
    if not isinstance(op, ir.Op):
        return None

    dtypes: List[str] = []
    ranks: List[int] = []
    shapes: List[List[int]] = []
    for arg in call.args:
        sinfo = arg.struct_info
        if not isinstance(sinfo, relax.TensorStructInfo):
            return None
        try:
            shape = _shape_to_int_list(sinfo.shape)
        except ValueError:
            return None
        dtypes.append(sinfo.dtype)
        ranks.append(len(shape))
        shapes.append(shape)

    return CallSiteInfo(
        op_name=op.name,
        input_dtypes=dtypes,
        input_ranks=ranks,
        input_shapes=shapes,
    )


# ----------------------------------------------------------------------
# Wrapper PrimFunc synthesis (per callsite)
# ----------------------------------------------------------------------

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
    """Build a buffer shape with **int64** dims.

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

    # ``FuseTIR`` in the Relax zero pipeline expects called PrimFuncs to be
    # schedulable (root SBlockRealize body). Wrap the extern call accordingly.
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


# ----------------------------------------------------------------------
# Mutator: rewrite Relax calls -> R.call_tir(extern_wrapper, ...)
# ----------------------------------------------------------------------

@mutator
class InjectCustomKernelsMutator(PyExprMutator):
    """Rewrites matched Relax calls to ``R.call_tir`` of synthesized wrappers.

    A separate wrapper PrimFunc is generated per unique
    ``(kernel_name, input_shapes, output_shape)`` tuple, so different
    callsites of the same op (e.g. fc1 vs fc2 ``relax.matmul``) get
    distinct, shape-specialized wrappers around the same C symbol.

    The pass also accumulates the set of kernels actually used, so
    downstream build code can link only the necessary C sources.
    """

    def __init__(self, mod: ir.IRModule, catalog: KernelCatalog):
        super().__init__(mod)
        self._mod = mod
        self._catalog = catalog
        self._cache: Dict[Tuple, ir.GlobalVar] = {}
        self._used_kernels: Dict[str, KernelDef] = {}

    @property
    def used_kernels(self) -> List[KernelDef]:
        return list(self._used_kernels.values())

    def _wrapper_symbol(self, kernel: KernelDef, idx: int) -> str:
        return f"extern_{kernel.c_function_name}_{idx}"

    def visit_call_(self, call: relax.Call) -> relax.Expr:  # noqa: D401
        call = super().visit_call_(call)

        site = _extract_callsite_info(call)
        if site is None:
            return call

        rule = select_rule(self._catalog, site)
        if rule is None:
            return call

        kernel = self._catalog.kernels_for_rule(rule)

        if len(site.input_shapes) != kernel.num_inputs:
            return call

        try:
            output_shape = resolve_output_shape(rule.output, site)
        except ValueError:
            return call

        cache_key = (
            kernel.name,
            tuple(tuple(s) for s in site.input_shapes),
            tuple(output_shape),
            rule.output.dtype,
        )

        if cache_key not in self._cache:
            idx = len(self._cache)
            func_symbol = self._wrapper_symbol(kernel, idx)
            pf = make_extern_primfunc(
                kernel,
                [list(s) for s in site.input_shapes],
                list(output_shape),
                func_symbol,
            )
            gv = ir.GlobalVar(func_symbol)
            _update_struct_info(gv, relax.FuncStructInfo.opaque_func())
            self._mod[gv] = pf
            self._cache[cache_key] = gv
            self._used_kernels[kernel.name] = kernel

        gv = self._cache[cache_key]
        out_sinfo = relax.TensorStructInfo(tuple(output_shape), rule.output.dtype)
        return relax.call_tir(gv, list(call.args), out_sinfo=out_sinfo)


# ----------------------------------------------------------------------
# Public pass factory
# ----------------------------------------------------------------------

def inject_custom_kernels(catalog: KernelCatalog):
    """Module pass parameterized by the kernel catalog.

    Use::

        mod = inject_custom_kernels(catalog)(mod)
        mod = relax.get_pipeline("zero")(mod)

    Returns a TVM module pass. After running, the list of kernels
    actually selected for the model is available via
    ``catalog.used_kernels`` if a tracking accessor was attached
    (see ``inject_custom_kernels_tracked`` for that variant).
    """

    @ir.transform.module_pass(opt_level=0, name="InjectCustomKernels")
    def _pass(mod: ir.IRModule, _ctx) -> ir.IRModule:
        new_mod = ir.IRModule(
            {gv: func for gv, func in mod.functions.items()},
            attrs=mod.attrs,
        )
        mutator_inst = InjectCustomKernelsMutator(new_mod, catalog)
        for gv, func in list(new_mod.functions.items()):
            if isinstance(func, relax.Function):
                new_mod[gv] = mutator_inst.visit_expr(func)
        return new_mod

    return _pass


def inject_custom_kernels_tracked(
    catalog: KernelCatalog,
) -> Tuple[tvm.transform.Pass, "List[KernelDef]"]:
    """Like :func:`inject_custom_kernels` but also returns a list that gets
    populated with the kernels actually used by the rewritten module.

    This lets the build script link only the C sources that are
    actually invoked (instead of every kernel in the catalog).
    """
    used: List[KernelDef] = []

    @ir.transform.module_pass(opt_level=0, name="InjectCustomKernels")
    def _pass(mod: ir.IRModule, _ctx) -> ir.IRModule:
        new_mod = ir.IRModule(
            {gv: func for gv, func in mod.functions.items()},
            attrs=mod.attrs,
        )
        mutator_inst = InjectCustomKernelsMutator(new_mod, catalog)
        for gv, func in list(new_mod.functions.items()):
            if isinstance(func, relax.Function):
                new_mod[gv] = mutator_inst.visit_expr(func)
        used.clear()
        used.extend(mutator_inst.used_kernels)
        return new_mod

    return _pass, used
