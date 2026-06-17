"""JSON-driven, model-agnostic custom kernel catalog + rule engine.

This module replaces the older flat ``custom_kernels`` list with a
two-layer design:

  * ``kernels``  -- a name-keyed catalog of available external C kernels
                    (ABI, sources, include dirs, arg_layout).
  * ``rules``    -- ordered match rules that select a kernel for a given
                    Relax callsite based on op semantics + tensor
                    properties (dtype/rank), NOT on TIR function names.

This keeps the configuration **model-agnostic**: the same ``kernels.json``
can serve any model whose Relax IR contains the relevant ops/dtypes.

JSON schema (see ``kernels.json``)::

  {
    "version": "1.0",
    "kernels": {
      "<kernel_name>": {
        "c_function_name":   "fmatmul32",
        "source_file":       "apps/fmatmul/kernel/fmatmul32.c",
        "extra_sources":     [],
        "include_dirs":      [...],
        "host_compatible":   false,
        "buffer_signature":  ["float32*", "float32*", "float32*"],

        "shape_bindings": {
          "<var_name>": ["<buffer>", <axis_index>]
        },

        "arg_layout": [
          { "buffer":   "out" | "in0" | ... },
          { "scalar":   "int32" | "int64" | "float32" | "float64",
            "value":    <num> },
          { "shape_var": "<var_name>", "dtype": "int64" }
        ]
      }
    },

    "rules": [
      {
        "name":     "<rule_name>",
        "priority": 100,
        "match": {
          "relax_op":     ["relax.matmul", "relax.nn.dense"],
          "input_count":  2,
          "input_dtypes": ["float32", "float32"],
          "input_ranks":  [2, 2]
        },
        "kernel": "<kernel_name>",
        "output": {
          "dtype": "float32",
          "shape": "infer_matmul_2d"
                  | [1, 256]
        }
      }
    ],

    "policy": {
      "on_ambiguity": "highest_priority",
      "on_no_match":  "keep_original"
    }
  }
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


# ----------------------------------------------------------------------
# C type / dtype helpers
# ----------------------------------------------------------------------

_C_TYPE_TO_TVM_DTYPE = {
    "float64*": "float64", "float64": "float64",
    "float32*": "float32", "float32": "float32",
    "float16*": "float16", "float16": "float16",
    "int64*":   "int64",   "int64":   "int64",
    "int32*":   "int32",   "int32":   "int32",
    "int8*":    "int8",    "int8":    "int8",
}


def c_arg_to_dtype(c_type: str) -> str:
    """Map a C-style arg string (``float32*``) to a TVM dtype (``float32``)."""
    if c_type not in _C_TYPE_TO_TVM_DTYPE:
        raise ValueError(
            f"Unsupported C arg type '{c_type}'. "
            f"Add it to _C_TYPE_TO_TVM_DTYPE in kernels_config.py."
        )
    return _C_TYPE_TO_TVM_DTYPE[c_type]


# ----------------------------------------------------------------------
# arg_layout items: a tagged-union of buffer / scalar literal / shape var
# ----------------------------------------------------------------------

@dataclass
class BufferRef:
    """References one of the PrimFunc buffer params (``in0``...``inN-1`` or ``out``)."""
    name: str


@dataclass
class ScalarLiteral:
    """Inline numeric constant passed positionally to ``call_extern``."""
    dtype: str
    value: float


@dataclass
class ShapeVarRef:
    """Reference to a shape variable bound at match time via ``shape_bindings``.

    Resolved per callsite to a concrete dimension extracted from one of
    the input tensors' static shapes.
    """
    name: str
    dtype: str = "int64"


ArgLayoutItem = Union[BufferRef, ScalarLiteral, ShapeVarRef]


def _parse_arg_layout(raw: List[Dict]) -> List[ArgLayoutItem]:
    out: List[ArgLayoutItem] = []
    for entry in raw:
        if "buffer" in entry:
            out.append(BufferRef(name=entry["buffer"]))
        elif "scalar" in entry:
            out.append(ScalarLiteral(dtype=entry["scalar"], value=entry["value"]))
        elif "shape_var" in entry:
            out.append(ShapeVarRef(
                name=entry["shape_var"],
                dtype=entry.get("dtype", "int64"),
            ))
        else:
            raise ValueError(
                f"arg_layout entry must have 'buffer', 'scalar' or 'shape_var': {entry!r}"
            )
    return out


# ----------------------------------------------------------------------
# KernelDef: one kernel in the catalog (ABI + sources + arg_layout)
# ----------------------------------------------------------------------

# shape_bindings: var_name -> (buffer_name, axis_index)
ShapeBinding = Tuple[str, int]


@dataclass
class KernelDef:
    """One entry under ``kernels`` in ``kernels.json``."""

    name: str
    c_function_name: str
    source_file: str

    buffer_signature: List[str] = field(default_factory=list)
    extra_sources: List[str] = field(default_factory=list)
    include_dirs: List[str] = field(default_factory=list)
    arg_layout: List[ArgLayoutItem] = field(default_factory=list)
    shape_bindings: Dict[str, ShapeBinding] = field(default_factory=dict)
    host_compatible: bool = True

    @property
    def num_buffers(self) -> int:
        return len(self.buffer_signature)

    @property
    def num_inputs(self) -> int:
        return max(0, self.num_buffers - 1)

    @property
    def buffer_dtypes(self) -> List[str]:
        return [c_arg_to_dtype(s) for s in self.buffer_signature]

    def default_arg_layout(self) -> List[ArgLayoutItem]:
        """Legacy fallback: ``in0, in1, ..., out``."""
        return [BufferRef(f"in{i}") for i in range(self.num_inputs)] + [BufferRef("out")]

    def effective_arg_layout(self) -> List[ArgLayoutItem]:
        return list(self.arg_layout) if self.arg_layout else self.default_arg_layout()


def _parse_shape_bindings(raw: Dict[str, List]) -> Dict[str, ShapeBinding]:
    out: Dict[str, ShapeBinding] = {}
    for var, bind in raw.items():
        if not (isinstance(bind, (list, tuple)) and len(bind) == 2):
            raise ValueError(
                f"shape_bindings['{var}'] must be [buffer_name, axis_index], got {bind!r}"
            )
        out[var] = (str(bind[0]), int(bind[1]))
    return out


def _parse_kernel_def(name: str, raw: Dict[str, Any]) -> KernelDef:
    e = dict(raw)
    if "arg_layout" in e:
        e["arg_layout"] = _parse_arg_layout(e["arg_layout"])
    if "shape_bindings" in e:
        e["shape_bindings"] = _parse_shape_bindings(e["shape_bindings"])
    return KernelDef(name=name, **e)


# ----------------------------------------------------------------------
# Output shape policy
# ----------------------------------------------------------------------

@dataclass
class OutputSpec:
    """How to derive the rewritten ``call_tir`` ``out_sinfo``."""
    dtype: str
    shape: Union[List[int], str]   # literal list OR named inference policy

    def is_static(self) -> bool:
        return not isinstance(self.shape, str)


def _parse_output_spec(raw: Dict[str, Any], kernel: KernelDef) -> OutputSpec:
    dtype = raw.get("dtype")
    if dtype is None:
        if not kernel.buffer_signature:
            raise ValueError(
                f"Rule for kernel '{kernel.name}' has no output dtype "
                f"and the kernel has no buffer_signature to infer from."
            )
        dtype = c_arg_to_dtype(kernel.buffer_signature[-1])
    shape = raw.get("shape", "infer_from_first_input")
    if isinstance(shape, list):
        shape = [int(d) for d in shape]
    return OutputSpec(dtype=dtype, shape=shape)


# ----------------------------------------------------------------------
# KernelRule: match a Relax callsite -> select a kernel
# ----------------------------------------------------------------------

@dataclass
class MatchSpec:
    """Predicate over a Relax ``Call`` site."""
    relax_ops: List[str] = field(default_factory=list)
    input_count: Optional[int] = None
    input_dtypes: Optional[List[str]] = None  # exact, in argument order
    input_ranks:  Optional[List[int]] = None  # exact, in argument order


def _parse_match(raw: Dict[str, Any]) -> MatchSpec:
    relax_ops = raw.get("relax_op", [])
    if isinstance(relax_ops, str):
        relax_ops = [relax_ops]
    return MatchSpec(
        relax_ops=list(relax_ops),
        input_count=raw.get("input_count"),
        input_dtypes=raw.get("input_dtypes"),
        input_ranks=raw.get("input_ranks"),
    )


@dataclass
class KernelRule:
    """One entry under ``rules`` in ``kernels.json``."""
    name: str
    priority: int
    match: MatchSpec
    kernel: str          # KernelDef name
    output: OutputSpec   # how to derive out_sinfo


def _parse_rule(raw: Dict[str, Any], kernels: Dict[str, KernelDef]) -> KernelRule:
    kname = raw["kernel"]
    if kname not in kernels:
        raise ValueError(
            f"rule '{raw.get('name', '?')}' references unknown kernel '{kname}'. "
            f"Known: {sorted(kernels)}"
        )
    return KernelRule(
        name=raw.get("name", f"rule_for_{kname}"),
        priority=int(raw.get("priority", 0)),
        match=_parse_match(raw.get("match", {})),
        kernel=kname,
        output=_parse_output_spec(raw.get("output", {}), kernels[kname]),
    )


# ----------------------------------------------------------------------
# Catalog: kernels + rules + policy
# ----------------------------------------------------------------------

@dataclass
class CatalogPolicy:
    on_ambiguity: str = "highest_priority"
    on_no_match: str = "keep_original"


@dataclass
class KernelCatalog:
    kernels: Dict[str, KernelDef]
    rules: List[KernelRule]
    policy: CatalogPolicy = field(default_factory=CatalogPolicy)

    def kernels_for_rule(self, rule: KernelRule) -> KernelDef:
        return self.kernels[rule.kernel]

    def all_kernels(self) -> List[KernelDef]:
        return list(self.kernels.values())

    def rules_sorted(self) -> List[KernelRule]:
        return sorted(self.rules, key=lambda r: -r.priority)


def load_catalog(json_path: str | Path) -> KernelCatalog:
    """Parse ``kernels.json`` into a :class:`KernelCatalog`."""
    path = Path(json_path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "kernels" not in data or "rules" not in data:
        raise ValueError(f"{path}: JSON must contain 'kernels' and 'rules' keys.")

    kernels: Dict[str, KernelDef] = {}
    for kname, kraw in data["kernels"].items():
        kernels[kname] = _parse_kernel_def(kname, kraw)
    rules = [_parse_rule(r, kernels) for r in data["rules"]]
    policy_raw = data.get("policy", {})
    policy = CatalogPolicy(
        on_ambiguity=policy_raw.get("on_ambiguity", "highest_priority"),
        on_no_match=policy_raw.get("on_no_match", "keep_original"),
    )
    return KernelCatalog(kernels=kernels, rules=rules, policy=policy)


# ----------------------------------------------------------------------
# Match evaluation (pure-data; no TVM imports here)
# ----------------------------------------------------------------------

@dataclass
class CallSiteInfo:
    """Pre-extracted data about a Relax callsite, for rule evaluation."""
    op_name: str
    input_dtypes: Sequence[str]
    input_ranks: Sequence[int]
    input_shapes: Sequence[Sequence[int]]


# ----------------------------------------------------------------------
# Output shape inference policies
# ----------------------------------------------------------------------

def infer_output_shape(policy: str, site: CallSiteInfo) -> List[int]:
    """Resolve a named output shape policy against a callsite."""
    if policy == "infer_matmul_2d":
        if len(site.input_shapes) < 2:
            raise ValueError("infer_matmul_2d needs 2 inputs")
        a, b = site.input_shapes[0], site.input_shapes[1]
        if len(a) != 2 or len(b) != 2:
            raise ValueError(
                f"infer_matmul_2d expects 2D inputs, got {a} x {b}"
            )
        return [int(a[0]), int(b[1])]

    if policy == "infer_from_first_input":
        if not site.input_shapes:
            raise ValueError("infer_from_first_input needs at least 1 input")
        return [int(d) for d in site.input_shapes[0]]

    raise ValueError(f"Unknown shape inference policy: {policy!r}")


def resolve_output_shape(spec: OutputSpec, site: CallSiteInfo) -> List[int]:
    if spec.is_static():
        return [int(d) for d in spec.shape]  # type: ignore[arg-type]
    return infer_output_shape(spec.shape, site)  # type: ignore[arg-type]


# ----------------------------------------------------------------------
# Quick sanity dump (CLI)
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "kernels.json"
    cat = load_catalog(path)
    print(f"Loaded {len(cat.kernels)} kernel(s) and {len(cat.rules)} rule(s) from {path}")
    for k in cat.kernels.values():
        print(f"  kernel {k.name}: {k.c_function_name} (src={k.source_file})")
    for r in cat.rules_sorted():
        print(f"  rule   {r.name}@{r.priority}: {r.match.relax_ops} -> {r.kernel}")
