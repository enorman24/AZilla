"""Model definition for quick_start: 2-layer MLP.

Pipeline is handled by ``pipeline/runner.py``.
"""
from tvm.relax.frontend import nn


class MLPModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 256)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(256, 10)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu1(x)
        x = self.fc2(x)
        return x


def get_model():
    return MLPModel()


def get_export_spec():
    return {"forward": {"x": nn.spec.Tensor((1, 784), "float32")}}
