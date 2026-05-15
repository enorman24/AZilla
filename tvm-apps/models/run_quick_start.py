from pathlib import Path
import tvm
from tvm import relax
from tvm.relax.frontend import nn

out_dir = Path('build/quick_start_artifacts')
out_dir.mkdir(parents=True, exist_ok=True)

class MLPModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 256)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(256, 10)
    def forward(self, x):
        return self.fc2(self.relu1(self.fc1(x)))

mod, _ = MLPModel().export_tvm(spec={"forward": {"x": nn.spec.Tensor((1, 784), "float32")}})
(out_dir / '00_exported_relax.py').write_text(mod.script(), encoding='utf-8')

mod_opt = relax.get_pipeline('zero')(mod)
(out_dir / '01_zero_pipeline_relax_tir.py').write_text(mod_opt.script(), encoding='utf-8')

ex = tvm.compile(mod_opt, tvm.target.Target('llvm'))
llvm_mod = ex.mod.imports[0] if len(ex.mod.imports) else ex.mod
(out_dir / '02_codegen.ll').write_text(llvm_mod.inspect_source('ll'), encoding='utf-8')
(out_dir / '03_codegen.s').write_text(llvm_mod.inspect_source('asm'), encoding='utf-8')

print(f"Wrote artifacts to {out_dir}")