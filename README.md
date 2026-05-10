<h1 align="center">AraXL: A Physically Scalable, Ultra-Wide RISC-V Vector Processor Design for Fast and Efficient Computation on Long Vectors</h1>

<a href="https://pulp-platform.org">
<img src="docs/source/images/pulp_logo_icon.svg" alt="Logo" width="100" align="right">
</a>

The scaled up Ara version AraXL is a vector unit working as a coprocessor for the CVA6 core.
It supports the RISC-V Vector Extension, [version 1.0](https://github.com/riscv/riscv-v-spec/releases/tag/v1.0).

AraXL architecture consists of multiple Ara instances (Ara2 - https://github.com/pulp-platform/ara) and each Ara2 cluster is a lane based vector processor. 
Multiple Ara2 clusters are interconnected with interfaces designed to access the L2 memory, other neighboring clusters and receive vector instructions from the CVA6 scalar core.

AraXL is developed as part of the [PULP (Parallel Ultra-Low Power) Platform](https://pulp-platform.org/), a joint effort between ETH Zurich and the University of Bologna.

## 📜 License
Unless specified otherwise in the respective file headers, all code in this repository is released under permissive licenses.
- Hardware sources and tool scripts are licensed under the [Solderpad Hardware License 0.51](LICENSE.hw) or compatible licenses.
- All software sources are licensed under [Apache 2.0](LICENSE.sw). Modified or reuse of external contributions and the licenses are listed in the [apps/README.md](apps/README.md).

## Dependencies

Check `DEPENDENCIES.md` for a list of hardware and software dependencies of Ara.

## Supported instructions

Check `FUNCTIONALITIES.md` to check which instructions are currently support by Ara.

## Get started

Use the one-shot bootstrap script to prepare a fresh checkout. It will sync and update submodules, build the GCC/LLVM toolchains, build Spike and Verilator, checkout the hardware IP dependencies, and apply the required hardware patches:

```bash
./scripts/get-started.sh
```

For incremental runs, you can skip specific stages. For example, if the toolchains are already built:

```bash
./scripts/get-started.sh --skip-gcc --skip-llvm --skip-spike --skip-verilator
```


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
fmatmul example for 32 lane configuration
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
make compile nr_clusters=4 nr_lanes=4
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

### VCD Dumping

For activity-based power analysis, use `vcd_dump=1` when compiling and simulating:

```bash
make -C apps bin/${program} vcd_dump=1
make -C hardware simc app=${program} vcd_dump=1
```

Supported kernels: `fmatmul`, `fconv3d`, `fft`, `dwt`, `exp`, `cos`, `log`, `dropout`, `jacobi2d`.

### Ideal Dispatcher mode

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

### Linting Flow

We also provide Synopsys Spyglass linting scripts in the hardware/spyglass. Run make lint in the hardware folder, with a specific MemPool configuration, to run the tests associated with the lint_rtl target.

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
