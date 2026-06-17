"""DPL-based pass that rewrites matched Relax ops to external C kernels.

For each rule in the JSON catalog (highest priority first):

  1. Build an ``is_op(op_name)(wildcard(), ...)`` pattern.
  2. Apply ``rewrite_call`` to every ``relax.Function`` in the module.
  3. Inside the callback, validate dtype/rank constraints from the rule.
     Return the original call unchanged if constraints are not met.
  4. Synthesize a TIR ``PrimFunc`` wrapper via ``make_extern_primfunc`` and
     replace the call with ``R.call_tir``.

Once rewritten, ``call_tir`` is not a Relax op, so lower-priority rules
cannot accidentally match the same site a second time.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import tvm
from tvm import ir, relax
from tvm import tirx as tir
from tvm.relax.dpl import wildcard, is_op, rewrite_call
from tvm.relax.expr import _update_struct_info

from .kernels_config import (
    KernelCatalog,
    KernelDef,
    KernelRule,
    resolve_output_shape,
    CallSiteInfo,
)
from .extern_primfunc import make_extern_primfunc


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


def _make_rewriter(
    rule: KernelRule,
    kernel: KernelDef,
    op_name: str,
    input_wildcards: List,
    new_mod: ir.IRModule,
    cache: Dict[Tuple, ir.GlobalVar],
    used_kernels: Dict[str, KernelDef],
):
    """Return a ``rewrite_call``-compatible callback for one rule/op pair."""

    def rewriter(matched_expr, matchings):
        call_args = [matchings[w] for w in input_wildcards]

        if rule.match.input_dtypes:
            for expected, arg in zip(rule.match.input_dtypes, call_args):
                if expected and arg.struct_info.dtype != expected:
                    return matched_expr

        if rule.match.input_ranks:
            for expected_rank, arg in zip(rule.match.input_ranks, call_args):
                if expected_rank and len(arg.struct_info.shape) != expected_rank:
                    return matched_expr

        try:
            input_shapes = [_shape_to_int_list(a.struct_info.shape) for a in call_args]
        except ValueError:
            return matched_expr

        if len(input_shapes) != kernel.num_inputs:
            return matched_expr

        site = CallSiteInfo(
            op_name=op_name,
            input_dtypes=[a.struct_info.dtype for a in call_args],
            input_ranks=[len(s) for s in input_shapes],
            input_shapes=input_shapes,
        )
        try:
            output_shape = resolve_output_shape(rule.output, site)
        except ValueError:
            return matched_expr

        cache_key = (
            kernel.name,
            tuple(tuple(s) for s in input_shapes),
            tuple(output_shape),
            rule.output.dtype,
        )
        if cache_key not in cache:
            idx = len(cache)
            func_symbol = f"extern_{kernel.c_function_name}_{idx}"
            pf = make_extern_primfunc(
                kernel,
                [list(s) for s in input_shapes],
                list(output_shape),
                func_symbol,
            )
            gv = ir.GlobalVar(func_symbol)
            _update_struct_info(gv, relax.FuncStructInfo.opaque_func())
            new_mod[gv] = pf
            cache[cache_key] = gv
            used_kernels[kernel.name] = kernel

        gv = cache[cache_key]
        out_sinfo = relax.TensorStructInfo(tuple(output_shape), rule.output.dtype)
        return relax.call_tir(gv, call_args, out_sinfo=out_sinfo)

    return rewriter


def inject_custom_kernels(
    catalog: KernelCatalog,
    *,
    used: Optional[List[KernelDef]] = None,
):
    """Module pass parameterized by the kernel catalog.

    Usage::

        mod = inject_custom_kernels(catalog)(mod)
        mod = relax.get_pipeline("zero")(mod)

    To track which kernels were actually used::

        used = []
        mod = inject_custom_kernels(catalog, used=used)(mod)
    """

    @ir.transform.module_pass(opt_level=0, name="InjectCustomKernels")
    def _pass(mod: ir.IRModule, _ctx) -> ir.IRModule:
        new_mod = ir.IRModule(
            {gv: func for gv, func in mod.functions.items()},
            attrs=mod.attrs,
        )
        cache: Dict[Tuple, ir.GlobalVar] = {}
        used_kernels: Dict[str, KernelDef] = {}

        for rule in catalog.rules_sorted():
            kernel = catalog.kernels_for_rule(rule)
            n_inputs = rule.match.input_count or kernel.num_inputs
            for op_name in (rule.match.relax_ops or []):
                input_wildcards = [wildcard() for _ in range(n_inputs)]
                pattern = is_op(op_name)(*input_wildcards)
                rewriter_fn = _make_rewriter(
                    rule, kernel, op_name, input_wildcards,
                    new_mod, cache, used_kernels,
                )
                for gv, func in list(new_mod.functions.items()):
                    if isinstance(func, relax.Function):
                        new_mod[gv] = rewrite_call(pattern, rewriter_fn, func)

        if used is not None:
            used.clear()
            used.extend(used_kernels.values())

        return new_mod

    return _pass
