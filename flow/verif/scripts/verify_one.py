#!/usr/bin/env python3
"""
verify_one.py - build ONE directed test kernel for both targets, run it on the
Spike reference oracle and on the AraXL Verilator RTL sim, and classify.

Differential oracle: the kernel prints its result region as raw hex between
markers. The SAME kernel body is built twice (Spike HTIF runtime / Verilator
common runtime) and run on both; Spike is golden, Verilator is the DUT.

Classification (per kernel):
  PASS            - Verilator printed '*** SUCCESS ***' AND its payload hex
                    matches Spike's payload hex exactly.
  FAIL_INCORRECT  - Verilator finished (SUCCESS, or FAILED with a non-illegal
                    trap) but payload != Spike, OR a non-illegal trap occurred.
  FAIL_HANG       - neither SUCCESS nor FAILED banner within the cycle cap /
                    wall-clock timeout (the false-PASS-on-hang case).
  BLOCKED         - Verilator '*** FAILED *** (tohost = 2)' (illegal-instruction
                    trap, mcause=2) while Spike ran the kernel fine -> the op is
                    not implemented / not decoded by AraXL.
  ERROR_BUILD / ERROR_SPIKE - infrastructure problems (could not build, or Spike
                    itself rejected the kernel) -> needs human attention.

Everything this script writes goes under <outdir> (isolated per kernel); the
shared inputs (runtime objects, linker script, sim binary) are read-only. This
satisfies the no-shared-mutable-file isolation requirement.

Usage:
  verify_one.py --kernel K.c --meta K.meta.json --outdir DIR \
      [--ara-dir D] [--nr-lanes 4] [--nr-clusters 4] \
      [--cycle-cap 300000] [--wall 600] [--vlen 4096]
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time

BEGIN = "===VERIF-BEGIN==="
END = "===VERIF-END==="


def run(cmd, **kw):
    return subprocess.run(cmd, shell=isinstance(cmd, str),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True, **kw)


def build_flags(ara, nl, nc, vlen):
    cc = f"{ara}/install/riscv-llvm/bin/clang"
    builtins = f"{ara}/install/riscv-llvm/lib/linux/libclang_rt.builtins-riscv64.a"
    common = (
        f"-march=rv64gcv_zfh_zvfh -menable-experimental-extensions -mabi=lp64d "
        f"-mno-relax -fuse-ld=lld -mno-implicit-float -mcmodel=medany "
        f"-I{ara}/apps/common -I{ara}/flow/verif/kernels "
        f"-O3 -ffast-math -fno-common -fno-builtin-printf "
        f"-DNR_LANES={nl} -DVLEN={vlen} -DNR_CLUSTERS={nc} "
        f"-ffunction-sections -fdata-sections"
    )
    spike_cc = (common +
                f" -DPREALLOCATE=1 -DSPIKE=1 -I{ara}/apps/riscv-tests/env "
                f"-I{ara}/apps/riscv-tests/benchmarks/common")
    ld_common = f"-static -nostartfiles -lm -Wl,--gc-sections -nostdlib {builtins}"
    spike_ld = ld_common + f" -T{ara}/apps/riscv-tests/benchmarks/common/test.ld"
    spike_rt = (f"{ara}/apps/riscv-tests/benchmarks/common/crt.S.o.spike-llvm "
                f"{ara}/apps/riscv-tests/benchmarks/common/syscalls.c.o.spike-llvm "
                f"{ara}/apps/common/util.c.o.spike-llvm")
    # NOTE: serial-llvm.c.o is intentionally omitted; verif.h supplies its own
    # ordered _putchar (the stock serial.c drops coalesced MMIO byte stores).
    veril_rt = (f"{ara}/apps/common/crt0-llvm.S.o {ara}/apps/common/printf-llvm.c.o "
                f"{ara}/apps/common/string-llvm.c.o "
                f"{ara}/apps/common/util-llvm.c.o")
    veril_ld_script = f"{ara}/flow/verif/build/lib/link-nc{nc}-l{nl}.ld"
    return dict(cc=cc, common=common, spike_cc=spike_cc, ld_common=ld_common,
                spike_ld=spike_ld, spike_rt=spike_rt, veril_rt=veril_rt,
                veril_ld_script=veril_ld_script)


def clean(s):
    # drop benign clang warnings from a compile/link log
    return "\n".join(l for l in s.splitlines()
                     if "unused during compilation" not in l
                     and "ignoring memory region" not in l)


def extract_payload(text):
    """lines strictly between the BEGIN and END markers, stripped of \\r."""
    lines = [l.rstrip("\r") for l in text.splitlines()]
    if BEGIN not in lines or END not in lines:
        return None
    b = lines.index(BEGIN)
    e = lines.index(END)
    if e <= b:
        return None
    return lines[b + 1:e]


_SIM_MARKERS = ("*** SUCCESS ***", "*** FAILED ***", "[hw-cycles]",
                "Received $finish", "Simulation statistics", "Simulation timeout")


def dut_payload_lines(log):
    """Kernel-emitted lines from the DUT log: from after BEGIN up to END, or (if
    the run trapped/hung before END) up to the first sim-status banner."""
    lines = [l.rstrip("\r") for l in log.splitlines()]
    if BEGIN not in lines:
        return []
    start = lines.index(BEGIN) + 1
    out = []
    for l in lines[start:]:
        if l == END:
            break
        if any(m in l for m in _SIM_MARKERS):
            break
        out.append(l)
    return out


def parse_blocks(payload):
    """split a payload (list of lines) into ordered (label, datatuple) variant
    blocks delimited by '#V <label>' lines. Lines before the first #V are ignored."""
    blocks = []
    label, data = None, []
    for l in payload:
        if l.startswith("#V "):
            if label is not None:
                blocks.append((label, tuple(data)))
            label, data = l[3:].strip(), []
        elif label is not None:
            data.append(l)
    if label is not None:
        blocks.append((label, tuple(data)))
    return blocks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kernel", required=True)
    ap.add_argument("--meta", default=None)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--ara-dir", default="/mnt/ssd/enorman/AZilla")
    ap.add_argument("--nr-lanes", type=int, default=4)
    ap.add_argument("--nr-clusters", type=int, default=4)
    ap.add_argument("--vlen", type=int, default=4096)
    ap.add_argument("--cycle-cap", type=int, default=200000)
    ap.add_argument("--wall", type=int, default=350)
    args = ap.parse_args()

    ara = os.path.abspath(args.ara_dir)
    args.outdir = os.path.abspath(args.outdir)
    args.kernel = os.path.abspath(args.kernel)
    os.makedirs(args.outdir, exist_ok=True)
    name = os.path.splitext(os.path.basename(args.kernel))[0]
    f = build_flags(ara, args.nr_lanes, args.nr_clusters, args.vlen)

    meta = {}
    if args.meta and os.path.exists(args.meta):
        meta = json.load(open(args.meta))

    res = {
        "name": name, "kernel": os.path.relpath(args.kernel, ara),
        "mnemonic": meta.get("mnemonic", name), "group": meta.get("group", ""),
        "ext": meta.get("ext", ""), "expected": meta.get("expected", ""),
        "variants": meta.get("variants", []), "note": "",
        "status": "ERROR_BUILD", "hw_cycles": None, "exec_cycles": None,
        "cycle_cap": args.cycle_cap, "wall_s": None,
        "nr_lanes": args.nr_lanes, "nr_clusters": args.nr_clusters,
        "vlen": args.vlen,
        "spike_elf": "", "veril_elf": "", "asm_ir": "", "dump_ir": "",
        "spike_out": "", "sim_log": "",
    }
    od = args.outdir

    # ---- build spike ELF ----
    s_o = f"{od}/{name}.spike.o"
    s_elf = f"{od}/{name}.spike-llvm"
    r = run(f'{f["cc"]} {f["spike_cc"]} -c {shlex.quote(args.kernel)} -o {s_o}')
    if r.returncode != 0:
        res["note"] = "spike compile failed: " + clean(r.stderr)[:400]
        json.dump(res, open(f"{od}/result.json", "w"), indent=2); print(res["status"]); return
    r = run(f'{f["cc"]} {f["spike_cc"]} -o {s_elf} {s_o} {f["spike_rt"]} {f["spike_ld"]}')
    if r.returncode != 0:
        res["note"] = "spike link failed: " + clean(r.stderr)[:400]
        json.dump(res, open(f"{od}/result.json", "w"), indent=2); print(res["status"]); return
    res["spike_elf"] = os.path.relpath(s_elf, ara)

    # ---- build verilator ELF + IR (.s asm, .dump disasm) ----
    v_o = f"{od}/{name}.veril.o"
    v_elf = f"{od}/{name}.elf"
    run(f'{f["cc"]} {f["common"]} -S -o {od}/{name}.s {shlex.quote(args.kernel)}')   # IR: assembly
    r = run(f'{f["cc"]} {f["common"]} -c {shlex.quote(args.kernel)} -o {v_o}')
    if r.returncode != 0:
        res["note"] = "verilator compile failed: " + clean(r.stderr)[:400]
        json.dump(res, open(f"{od}/result.json", "w"), indent=2); print(res["status"]); return
    if not os.path.exists(f["veril_ld_script"]):
        res["note"] = "missing linker script " + f["veril_ld_script"]
        json.dump(res, open(f"{od}/result.json", "w"), indent=2); print(res["status"]); return
    r = run(f'{f["cc"]} {f["common"]} -o {v_elf} {v_o} {f["veril_rt"]} {f["ld_common"]} -T {f["veril_ld_script"]}')
    if r.returncode != 0:
        res["note"] = "verilator link failed: " + clean(r.stderr)[:400]
        json.dump(res, open(f"{od}/result.json", "w"), indent=2); print(res["status"]); return
    res["veril_elf"] = os.path.relpath(v_elf, ara)
    run(f'{ara}/install/riscv-llvm/bin/llvm-objdump -d --mattr=v {v_elf} > {od}/{name}.dump 2>/dev/null')
    res["asm_ir"] = os.path.relpath(f"{od}/{name}.s", ara)
    res["dump_ir"] = os.path.relpath(f"{od}/{name}.dump", ara)

    # ---- run Spike (golden) ----
    spike = f"{ara}/install/riscv-isa-sim/bin/spike"
    r = run(f'timeout 120 {spike} --isa=rv64gcv_zfh --varch=vlen:{args.vlen},elen:64 {s_elf}')
    open(f"{od}/spike.out", "w").write(r.stdout + ("\n[stderr]\n" + r.stderr if r.stderr else ""))
    res["spike_out"] = os.path.relpath(f"{od}/spike.out", ara)
    spike_payload = extract_payload(r.stdout)
    if r.returncode != 0 or spike_payload is None:
        res["status"] = "ERROR_SPIKE"
        res["note"] = f"spike rc={r.returncode}; payload={'none' if spike_payload is None else len(spike_payload)} lines; " + (r.stderr[:200] if r.stderr else "")
        json.dump(res, open(f"{od}/result.json", "w"), indent=2); print(res["status"]); return

    # ---- run Verilator (DUT) in isolated cwd ----
    vbin = f"{ara}/hardware/build-nc{args.nr_clusters}-l{args.nr_lanes}/verilator/Vara_tb_verilator"
    sim_log = f"{od}/sim.log"
    t0 = time.time()
    rv = run(f'cd {shlex.quote(od)} && timeout {args.wall} {vbin} -c {args.cycle_cap} -l ram,{v_elf},elf > sim.log 2>&1')
    res["wall_s"] = round(time.time() - t0, 1)
    res["sim_log"] = os.path.relpath(sim_log, ara)
    log = open(sim_log).read() if os.path.exists(sim_log) else ""

    m = re.search(r"\[hw-cycles\]:\s*(\d+)", log)
    if m: res["hw_cycles"] = int(m.group(1))
    m = re.search(r"Executed cycles:\s*(\d+)", log)
    if m: res["exec_cycles"] = int(m.group(1))

    success = "*** SUCCESS ***" in log
    fm = re.search(r"\*\*\* FAILED \*\*\* \(tohost = (\d+)\)", log)
    timed_out = ("Simulation timeout of" in log) or (rv.returncode == 124)
    cause = int(fm.group(1)) if fm else None
    res["mcause"] = cause

    # how the DUT run terminated (used to label the first variant the DUT did
    # not complete): trap-illegal -> BLOCKED, other trap -> FAIL_INCORRECT, no
    # banner -> FAIL_HANG.
    if cause == 2:
        trunc_status, trunc_note = "BLOCKED", "illegal-instruction trap (mcause=2); not decoded by AraXL"
    elif cause is not None:
        trunc_status, trunc_note = "FAIL_INCORRECT", f"trap mcause={cause} (4/6=misaligned,5/7=access-fault)"
    elif timed_out:
        trunc_status, trunc_note = "FAIL_HANG", f"hang: cycle-cap={args.cycle_cap}/wall={args.wall}s reached, no banner"
    else:
        trunc_status, trunc_note = "FAIL_HANG", f"no SUCCESS/FAILED banner (rc={rv.returncode})"

    spike_blocks = parse_blocks(spike_payload)
    dut_blocks = {lbl: data for lbl, data in parse_blocks(dut_payload_lines(log))}

    # Per-variant verdicts, in spike (== kernel) order.
    vres = []
    truncated = False
    for lbl, sdata in spike_blocks:
        if truncated:
            vres.append({"variant": lbl, "status": "UNTESTED", "note": "after first trap/hang"})
        elif lbl in dut_blocks:
            if dut_blocks[lbl] == sdata:
                vres.append({"variant": lbl, "status": "PASS", "note": ""})
            else:
                vres.append({"variant": lbl, "status": "FAIL_INCORRECT",
                             "note": f"differs vs Spike: spike={sdata} dut={dut_blocks[lbl]}"})
        else:
            # first variant the DUT did not produce -> attribute the termination
            vres.append({"variant": lbl, "status": trunc_status, "note": trunc_note})
            truncated = True
    res["variant_results"] = vres

    # kernel-level rollup: worst by severity, plus per-status counts.
    sev = ["FAIL_INCORRECT", "FAIL_HANG", "BLOCKED", "UNTESTED", "PASS"]
    counts = {}
    for v in vres:
        counts[v["status"]] = counts.get(v["status"], 0) + 1
    res["variant_counts"] = counts
    if not vres:
        # nothing parsed: fall back to run-level termination
        res["status"] = "PASS" if (success and not spike_blocks) else trunc_status
        res["note"] = "no #V blocks parsed; " + (trunc_note if not success else "kernel emitted no variants")
    else:
        worst = min((v["status"] for v in vres), key=lambda s: sev.index(s) if s in sev else 99)
        res["status"] = worst
        res["note"] = (f"{counts.get('PASS',0)}/{len(vres)} variants PASS; "
                       + ", ".join(f"{k}:{counts[k]}" for k in sev if counts.get(k) and k != 'PASS'))
        bad = next((v for v in vres if v["status"] not in ("PASS",)), None)
        if bad:
            res["note"] += f" | first non-PASS '{bad['variant']}': {bad['note'][:120]}"

    json.dump(res, open(f"{od}/result.json", "w"), indent=2)
    print(f'{res["status"]:14s} {res["mnemonic"]:14s} {counts} hw={res["hw_cycles"]} wall={res["wall_s"]}s')


if __name__ == "__main__":
    main()
