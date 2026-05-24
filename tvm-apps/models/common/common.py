import tvm
import os


CURR_DIR = os.path.join(os.path.dirname(__file__))


target = tvm.target.Target({
    "kind": "llvm", # llvm backend
    "mtriple": "riscv64-unknown-elf", # Target / what representation to bring it down to
    "mattr": ["+v", "+m", "+f", "+d"], # vector extension, mult/div, single-precision float, double-precision float
    "mabi": "lp64d" # depends on the araxl toolchain -> May be changed
})


def save_kernel(name: str, lib):
    OUTPUT_DIR = os.path.join(CURR_DIR, "../../", "artifacts/output", name)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # print(lib.inspect_source())

    with open(os.path.join(OUTPUT_DIR, f"{name}.s"), "w") as f:
        f.write(lib.inspect_source("asm"))


    with open(os.path.join(OUTPUT_DIR, f"{name}.ll"), "w") as f:
        f.write(lib.inspect_source("ll"))
        