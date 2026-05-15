"""JSON parser for the custom kernel registry.

Schema (see ``kernels.json``):

  {
    "custom_kernels": [
      {
        "relax_op":         "relax.nn.conv2d",
        "c_function_name":  "fconv2d_3x3",
        "source_file":      "../apps/fconv2d/fconv2d_3x3.c",

        // optional:
        "extra_sources":    ["..."],          // additional .c files to link
        "include_dirs":     ["..."],          // -I dirs for the C build step

        // Required: dtypes of the **buffer** arguments, in TVM call order
        // (inputs first, output last).
        "args_signature":   ["float64*", "float64*", "float64*"],

        // Required: dtype + shape of the output tensor TVM will allocate.
        "out_dtype":        "float64",
        "target_shape":     [1, 1, 16, 16],

        // Optional: ordered list describing how the synthesized
        // ``T.call_extern`` should pass arguments to the C function.
        // Each entry is one of:
        //   { "buffer": "in0" | "in1" | ... | "out" }  -- pass buffer.data
        //   { "scalar": "int32" | "int64" | "float32" | "float64", "value": <num> }
        // If omitted, defaults to ``[in0, in1, ..., out]`` (legacy order).
        "arg_layout":       [...]
      }
    ]
  }
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union


_C_TYPE_TO_TVM_DTYPE = {
    "float64*": "float64",
    "float64":  "float64",
    "float32*": "float32",
    "float32":  "float32",
    "float16*": "float16",
    "float16":  "float16",
    "int64*":   "int64",
    "int64":    "int64",
    "int32*":   "int32",
    "int32":    "int32",
    "int8*":    "int8",
    "int8":     "int8",
}


def c_arg_to_dtype(c_type: str) -> str:
    """Map a C-style arg string (``float64*``) to a TVM dtype (``float64``)."""
    if c_type not in _C_TYPE_TO_TVM_DTYPE:
        raise ValueError(
            f"Unsupported C arg type '{c_type}'. "
            f"Add it to _C_TYPE_TO_TVM_DTYPE in kernels_config.py."
        )
    return _C_TYPE_TO_TVM_DTYPE[c_type]


@dataclass
class BufferRef:
    """Refers to one of the PrimFunc buffer params (``in0``...``inN-1`` or ``out``)."""
    name: str


@dataclass
class ScalarLiteral:
    """Inline numeric constant passed positionally to call_extern."""
    dtype: str
    value: float


ArgLayoutItem = Union[BufferRef, ScalarLiteral]


def _parse_arg_layout(raw: List[Dict]) -> List[ArgLayoutItem]:
    out: List[ArgLayoutItem] = []
    for entry in raw:
        if "buffer" in entry:
            out.append(BufferRef(name=entry["buffer"]))
        elif "scalar" in entry:
            out.append(ScalarLiteral(dtype=entry["scalar"], value=entry["value"]))
        else:
            raise ValueError(f"arg_layout entry must have 'buffer' or 'scalar': {entry!r}")
    return out


@dataclass
class KernelSpec:
    """One row of the custom kernel registry."""

    relax_op: str
    c_function_name: str
    source_file: str

    args_signature: List[str] = field(default_factory=list)
    target_shape: List[int]  = field(default_factory=list)

    out_dtype: Optional[str] = None
    extra_sources: List[str] = field(default_factory=list)
    include_dirs:  List[str] = field(default_factory=list)
    arg_layout:    List[ArgLayoutItem] = field(default_factory=list)
    host_compatible: bool = True

    @property
    def num_buffers(self) -> int:
        return len(self.args_signature)

    @property
    def num_inputs(self) -> int:
        return max(0, self.num_buffers - 1)

    @property
    def buffer_dtypes(self) -> List[str]:
        """TVM dtype for each buffer arg in ``args_signature`` (inputs + output)."""
        return [c_arg_to_dtype(s) for s in self.args_signature]

    @property
    def output_dtype(self) -> str:
        if self.out_dtype:
            return self.out_dtype
        if not self.args_signature:
            raise ValueError(f"{self.c_function_name}: empty args_signature")
        return c_arg_to_dtype(self.args_signature[-1])

    def default_arg_layout(self) -> List[ArgLayoutItem]:
        """Legacy order: in0, in1, ..., out (no scalars)."""
        return [BufferRef(f"in{i}") for i in range(self.num_inputs)] + [BufferRef("out")]

    def effective_arg_layout(self) -> List[ArgLayoutItem]:
        return list(self.arg_layout) if self.arg_layout else self.default_arg_layout()


def load_kernels(json_path: str | Path) -> List[KernelSpec]:
    path = Path(json_path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "custom_kernels" not in data:
        raise ValueError(f"{path}: missing top-level 'custom_kernels' array")

    out: List[KernelSpec] = []
    for entry in data["custom_kernels"]:
        e = dict(entry)
        if "arg_layout" in e:
            e["arg_layout"] = _parse_arg_layout(e["arg_layout"])
        out.append(KernelSpec(**e))
    return out


def specs_by_op(specs: List[KernelSpec]) -> Dict[str, KernelSpec]:
    out: Dict[str, KernelSpec] = {}
    for s in specs:
        if s.relax_op in out:
            raise ValueError(
                f"Duplicate Relax op '{s.relax_op}' in registry; "
                f"only one custom kernel per op is supported."
            )
        out[s.relax_op] = s
    return out


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "kernels.json"
    for spec in load_kernels(path):
        print(spec)
