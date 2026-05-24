import torch
from typing import Any
from torch import nn as torch_nn
from torch.export import export
import tvm
from tvm import relax
from tvm.relax.frontend.torch import from_exported_program

_TORCH_DTYPE_BY_NAME = {
    "float16": torch.float16,
    "float32": torch.float32,
    "float64": torch.float64,
    "int32": torch.int32,
    "int64": torch.int64,
}


def _make_example_args_from_spec(spec: dict[str, Any]) -> tuple[torch.Tensor]:
    """Create torch.export example args from TVM-style export spec."""
    tensor_spec = spec["forward"]["x"]
    shape = tuple(int(dim) for dim in tensor_spec.shape)
    dtype_name = str(tensor_spec.dtype)
    torch_dtype = _TORCH_DTYPE_BY_NAME.get(dtype_name)
    if torch_dtype is None:
        raise ValueError(f"Unsupported dtype in export spec: {dtype_name}")
    return (torch.randn(*shape, dtype=torch_dtype),)


class ExportableTorchModel:
    """Adapter so a PyTorch model can satisfy get_model() contract."""

    def __init__(self, model: torch_nn.Module):
        self.model = model.eval()

    def export_tvm(self, spec: dict[str, Any]):
        example_args = _make_example_args_from_spec(spec)
        with torch.no_grad():
            exported_program = export(self.model, example_args)
            mod = from_exported_program(
                exported_program,
                keep_params_as_input=True,
                unwrap_unit_return_tuple=True,
            )
        return relax.frontend.detach_params(mod)
