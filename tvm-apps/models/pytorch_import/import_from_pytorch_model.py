from __future__ import annotations

from typing import Any

import torch
from torch import nn as torch_nn
from torch.export import export

import tvm
from tvm import relax
from tvm.relax.frontend import nn as tvm_nn
from tvm.relax.frontend.torch import from_exported_program

from custom_pipeline.torch_adapter import ExportableTorchModel

class TorchModel(torch_nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = torch_nn.Linear(784, 256)
        self.relu1 = torch_nn.ReLU()
        self.fc2 = torch_nn.Linear(256, 10)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu1(x)
        x = self.fc2(x)
        return x

def get_model():
    return ExportableTorchModel(TorchModel())


def get_export_spec():
    return {"forward": {"x": tvm_nn.spec.Tensor((1, 784), "float32")}}


def build_relax_model() -> tvm.IRModule:
    mod, _params = get_model().export_tvm(spec=get_export_spec())
    return mod