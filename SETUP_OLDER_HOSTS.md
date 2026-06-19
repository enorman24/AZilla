# AraXL Setup on Older Hosts (RHEL/CentOS 7)

On RHEL/CentOS 7 (GLIBC 2.17) the system GCC, CMake, and Python are too old to
build the toolchains. This guide installs newer versions locally and works
around two LLVM-build issues. Run everything inside `tmux` so long builds
survive disconnects (`tmux new -s araxl`, reattach with `tmux attach -d -t araxl`).

## 1. Newer GCC (devtoolset-7)

The default GCC 4.8.5 fails to build binutils. Enable GCC 7.3.1:

```bash
scl enable devtoolset-7 bash
gcc --version   # expect 7.3.1
```

## 2. CMake ≥ 3.20 (local)

```bash
mkdir -p "$HOME/opt" && cd "$HOME/opt"
wget https://github.com/Kitware/CMake/releases/download/v3.28.6/cmake-3.28.6-linux-x86_64.tar.gz
tar -xzf cmake-3.28.6-linux-x86_64.tar.gz
```

## 3. Ninja (local)

```bash
mkdir -p "$HOME/opt/ninja" && cd "$HOME/opt/ninja"
wget https://github.com/ninja-build/ninja/releases/download/v1.12.1/ninja-linux.zip
unzip ninja-linux.zip && chmod +x ninja
export PATH="$HOME/opt/ninja:$PATH"
```

## 4. Python ≥ 3.8 (local)

The newest Miniconda won't run on GLIBC 2.17, so use the Python 3.8 installer:

```bash
cd "$HOME"
wget https://repo.anaconda.com/miniconda/Miniconda3-py38_23.3.1-0-Linux-x86_64.sh
bash Miniconda3-py38_23.3.1-0-Linux-x86_64.sh -b -p "$HOME/miniconda3-py38"
export PATH="$HOME/miniconda3-py38/bin:$HOME/opt/ninja:$PATH"
python3 --version   # expect 3.8.16+
```

## 5. Let LLVM build with GCC 7.3.1

GCC 7.3.1 is below LLVM's supported minimum (7.4). In the root `Makefile`, add
the following to the `toolchain-llvm-main` CMake command (alongside the other
`-D` options, e.g. after `-DCMAKE_BUILD_TYPE=Release \`):

```make
-DLLVM_FORCE_USE_OLD_TOOLCHAIN=ON \
```

## 6. Build the GCC toolchain first

Build GCC on its own before touching LLVM:

```bash
cd /home/$USER/projects/AZilla
./scripts/get-started.sh \
  --skip-llvm --skip-spike --skip-verilator \
  --skip-hw-checkout --skip-hw-patches
```

## 7. Build LLVM and the rest

Apply the Makefile edit from step 5, then build the remaining components.
Point the build at the local CMake — the `CMAKE` variable must hold *only* the
executable path, no extra arguments:

```bash
CMAKE="$HOME/opt/cmake-3.28.6-linux-x86_64/bin/cmake" \
  ./scripts/get-started.sh --skip-sync --skip-gcc
```

The script is resumable: re-run with `--skip-*` flags to skip stages that
already completed (`--help` lists them all). Expected final output:

```text
==> AraXL bootstrap completed.
```

## 8. Verify the installation

```bash
cd apps
make bin/hello_world
file bin/hello_world   # statically linked 64-bit ELF
```

A successful build produces `bin/hello_world` and `bin/hello_world.dump`.

## Troubleshooting

**`ln: failed to create symbolic link .../lib/clang/20/lib/linux: File exists`** —
fixed in the `Makefile` (`ln -sfn`). If you hit it on an older checkout, verify
the existing link is valid and rerun:

```bash
readlink -f install/riscv-llvm/lib/clang/20/lib/linux
# should resolve to install/riscv-llvm/lib/linux
```

**`Cannot determine hardware patch state`** — the tech_cells_generic dep has
local changes or a conflicting version. Check whether the patch is already
applied (no output = applied):

```bash
git -C hardware/deps/tech_cells_generic apply --reverse --check \
  "$PWD/hardware/patches/0001-tech-cells-generic-sram.patch"
```

## Caveat

GCC 7.3.1 is below LLVM's supported minimum. The `LLVM_FORCE_USE_OLD_TOOLCHAIN`
override worked here, but GCC 7.4+ is preferable when available.
