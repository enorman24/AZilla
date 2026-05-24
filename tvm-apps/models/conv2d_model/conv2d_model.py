from pathlib import Path
import tvm
from tvm import relax
from tvm.relax.frontend import nn

# out_dir = Path('build/quick_start_artifacts')
# out_dir.mkdir(parents=True, exist_ok=True)

class MLPModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2D(
            in_channels=1,
            out_channels=1,
            kernel_size=3,
            stride=1,
            padding=0,
            bias=False,
            dtype="float64",
        )

    def forward(self, x):
        return self.conv(x)

def get_model():
    return MLPModel()
def get_export_spec():
    return {"forward": {"x": nn.spec.Tensor((1, 1, 18, 18), "float64")}}
