"""Tiny 2-layer MLP for AraXL pipeline validation.

  x (4,16) -> Linear(16->32) -> ReLU -> Linear(32->8) -> logits (4,8)

Realistic as a small sensor-data classifier (e.g. 16 IMU features -> 8 classes).
The DPL pass replaces both matmul ops with fmatmul32 and both bias adds with
fbiasadd32. The weight transposes (512 + 256 scalar ops) and relu (128 ops)
are left to TVM — all three are tiny and fast in Verilator simulation.
"""
from tvm.relax.frontend import nn


class TinyMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1  = nn.Linear(16, 32)
        self.relu = nn.ReLU()
        self.fc2  = nn.Linear(32, 8)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x


def get_model():
    return TinyMLP()


def get_export_spec():
    return {"forward": {"x": nn.spec.Tensor((4, 16), "float32")}}
