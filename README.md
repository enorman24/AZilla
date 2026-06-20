# AraXL: A Physically Scalable, Ultra-Wide RISC-V Vector Processor Design for Fast and Efficient Computation on Long Vectors

The scaled up Ara version AraXL is a vector unit working as a coprocessor for the CVA6 core.
It supports the RISC-V Vector Extension, [version 1.0](https://github.com/riscv/riscv-v-spec/releases/tag/v1.0).

AraXL architecture consists of multiple Ara instances (Ara2 - https://github.com/pulp-platform/ara) and each Ara2 cluster is a lane based vector processor.
Multiple Ara2 clusters are interconnected with interfaces designed to access the L2 memory, other neighboring clusters and receive vector instructions from the CVA6 scalar core.

AraXL is developed as part of the [PULP (Parallel Ultra-Low Power) Platform](https://pulp-platform.org/), a joint effort between ETH Zurich and the University of Bologna.

## For new contributors

### 1. Clone the repository

```bash
git clone git@github.com:enorman24/AZilla.git
cd AZilla
```

(If you have not set up SSH keys with GitHub, use the HTTPS URL from the repo's
green **Code** button instead.)

### 2. Create your own branch before editing

Never commit directly to the default branch. Create a branch for your work:

```bash
git switch -c <your-branch-name>
```

Push it (once you have collaborator access) with:

```bash
git push -u origin <your-branch-name>
```

### 3. Follow the rest of the setup, in order

1. **Build the toolchain and hardware deps** — the [Get started](#get-started)
   section below (`./scripts/get-started.sh`).
2. **Set up the compiler software stack (TVM / TileLang)** — see
   [SOFTWARE.md](SOFTWARE.md).
3. **Build, simulate, and debug TVM kernels on AraXL** — see
   [tvm-apps/README.md](tvm-apps/README.md), which walks through configuring,
   verilating, simulating the `fdotproduct` kernel (default in `tvm-apps/config.mk`), and waveform debugging.

> **Tip:** Long-running steps (toolchain builds, verilation, RTL simulation)
> should be run inside [tmux](https://github.com/tmux/tmux/wiki) so they survive
> SSH disconnects. Start a session with `tmux`, run your command, detach with
> `Ctrl-b d`, and reattach later with `tmux attach`.

## 📜 License

Unless specified otherwise in the respective file headers, all code in this repository is released under permissive licenses.

- Hardware sources and tool scripts are licensed under the [Solderpad Hardware License 0.51](LICENSE.hw) or compatible licenses.
- All software sources are licensed under [Apache 2.0](LICENSE.sw). Modified or reuse of external contributions and the licenses are listed in the [apps/README.md](apps/README.md).

## Dependencies

Check `DEPENDENCIES.md` for a list of hardware and software dependencies of AZilla/AraXL.

## Supported instructions

Check `FUNCTIONALITIES.md` to check which instructions are supported by AraXL.

## Prerequisites

The bootstrap builds the GCC/LLVM toolchains from source, so the host needs:

- **GCC ≥ 7.4** (the LLVM revision's minimum; the system compiler on RHEL/CentOS 7 is too old)
- **CMake ≥ 3.20**
- **Ninja**
- **Python ≥ 3.8**

> **Older hosts (RHEL/CentOS 7, GLIBC 2.17):** the system GCC, CMake, and Python
> are too old. See [SETUP_OLDER_HOSTS.md](SETUP_OLDER_HOSTS.md) for a step-by-step
> workaround.

## Get started

This is the first build step after cloning. The one-shot bootstrap script prepares a
fresh checkout by running these stages in order:

1. Sync and update Git submodules.
2. Build the GCC and LLVM toolchains.
3. Build Spike (ISA simulator) and Verilator (RTL simulator).
4. Check out the hardware IP dependencies (via Bender).
5. Apply the required hardware patches.

Run it from the repository root:

```bash
./scripts/get-started.sh
```

> **Tip:** This takes a while (the toolchain builds dominate). Run it inside
> [tmux](https://github.com/tmux/tmux/wiki) so it survives SSH disconnects. The
> script is resumable — pass `--skip-sync`, `--skip-gcc`, `--skip-llvm`, etc. to
> re-run only the stages you need (`--help` lists them all).

## Configuration

Ara's parameters are centralized in the `config` folder, which provides several configurations to the vector machine.
Please check `config/README.md` for more details. This sets the number of lanes and the `VLEN` per Ara cluster.

By default the number of clusters is 2 and the number of lanes per clusters is 4 for an 8 lane AraXL configuration.

To change the configuration set `nr_clusters=4` and `nr_lanes=4` when compiling applications or hardware.

Prepend `config=chosen_ara_configuration` to your Makefile commands, or export the `ARA_CONFIGURATION` variable, to chose a configuration other than the `default` one.

## Software

### Build Applications

The `apps` folder contains example applications that work on Ara. Run the following command to build an application. E.g., `hello_world`:

```bash
cd apps
make bin/hello_world
```

fmatmul example for 16 lane configuration

```
make bin/fmatmul nr_clusters=4 nr_lanes=4
```

### SPIKE Simulation

All applications can be simulated with SPIKE:

```bash
cd apps
make bin/hello_world.spike
make spike-run-hello_world
```

### RISC-V Tests

To run the standardized [riscv-tests](https://github.com/riscv-software-src/riscv-tests) for AraXL:

```bash
make riscv_unit_tests
```

This downloads the riscv-tests repository, builds all unit tests and benchmarks, and applies a patch to update the `tohost` memory location to AraXL's memory-mapped EOC register. The test binary can then be run from the `hardware/` folder:

```bash
make sim preload=<path-to-test-binary>
```

## RTL Simulation

### Hardware Dependencies

The hardware depends on external IPs managed by Bender. To install Bender and check out all IPs:

```bash
cd hardware
make checkout
```

### Patches

Some IPs need to be patched to work with Verilator. Run once after checking out deps (or after re-checking them out):

```bash
cd hardware
make apply-patches
```

### Simulation

For Synopsys VCS:

```bash
cd hardware
make apply-patches              # required: patches Bender deps (DRAM preload, etc.)
make compile_vcs nr_clusters=4 nr_lanes=4
app=hello_world make sim_vcs
make show_vcs
```

For Verilator:

```bash
cd hardware
make apply-patches
make verilate
app=hello_world make simv
```

Add `trace=1` to `verilate`, `simv`, or `riscv_tests_simv` to generate FST waveform traces (viewable with GTKWave).

To run all RISC-V unit tests with Verilator:

```bash
cd hardware
make verilate
make riscv_tests_simv
```

### VRF SRAM backend

By default the vector register file banks use a behavioral `tc_sram` model, so all
simulation works out of the box with no proprietary files. A GF12 hard-macro backend
can be opted into for synthesis/hardened simulation with `gf12_sram=1` and a private,
bring-your-own SRAM wrapper — see [`hardware/docs/GF12_SRAM.md`](hardware/docs/GF12_SRAM.md).

### Ideal Dispatcher mode

> **Note:** Ideal Dispatcher mode may not be working correctly right now. Use with caution.

CVA6 can be replaced by an ideal FIFO that dispatches the vector instructions to Ara with the maximum issue-rate possible.
In this mode, only Ara and its memory system affect performance.
This mode has some limitations:

- The dispatcher is a simple FIFO. Ara and the dispatcher cannot have complex interactions.
- Therefore, the vector program should be fire-and-forget. There cannot be runtime dependencies from the vector to the scalar code.
- Not all the vector instructions are supported, e.g., the ones that use the `rs2` register.

To compile a program and generate its vector trace:

```bash
cd apps
make bin/${program}.ideal nr_clusters=4 nr_lanes=4
```

This command will generate the `ideal` binary to be loaded in the L2 memory for the simulation (data accessed by the vector code).
To run the system in Ideal Dispatcher mode:

```bash
cd hardware
make sim app=${program} ideal_dispatcher=1 nr_clusters=4 nr_lanes=4
```

## Publications

If you want to use AraXL, you can cite us:

```
@INPROCEEDINGS{10992880,
  author={Purayil, Navaneeth Kunhi and Perotti, Matteo and Fischer, Tim and Benini, Luca},
  booktitle={2025 Design, Automation & Test in Europe Conference (DATE)}, 
  title={AraXL: A Physically Scalable, Ultra-Wide RISC-V Vector Processor Design for Fast and Efficient Computation on Long Vectors}, 
  year={2025},
  volume={},
  number={},
  pages={1-7},
  keywords={Scalability;Computer architecture;Parallel processing;Vectors;Energy efficiency;Registers;Computational efficiency;Vector processors;Kernel;Optimization;Vector processors;RISC-V;Scalability},
  doi={10.23919/DATE64628.2025.10992880}
}
```

```
@Article{Ara2020,
  author = {Matheus Cavalcante and Fabian Schuiki and Florian Zaruba and Michael Schaffner and Luca Benini},
  journal= {IEEE Transactions on Very Large Scale Integration (VLSI) Systems},
  title  = {Ara: A 1-GHz+ Scalable and Energy-Efficient RISC-V Vector Processor With Multiprecision Floating-Point Support in 22-nm FD-SOI},
  year   = {2020},
  volume = {28},
  number = {2},
  pages  = {530-543},
  doi    = {10.1109/TVLSI.2019.2950087}
}
```

```
@INPROCEEDINGS{9912071,
  author={Perotti, Matteo and Cavalcante, Matheus and Wistoff, Nils and Andri, Renzo and Cavigelli, Lukas and Benini, Luca},
  booktitle={2022 IEEE 33rd International Conference on Application-specific Systems, Architectures and Processors (ASAP)},
  title={A “New Ara” for Vector Computing: An Open Source Highly Efficient RISC-V V 1.0 Vector Processor Design},
  year={2022},
  volume={},
  number={},
  pages={43-51},
  doi={10.1109/ASAP54787.2022.00017}}
```

