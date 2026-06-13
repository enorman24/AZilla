"""Artifact manifest helpers for the AraXL TVM app Makefile."""

import argparse
import datetime
import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def _path(value: str) -> str:
    return str(Path(value).resolve()) if value else ""


def _tool_map(items: Iterable[str]) -> Dict[str, str]:
    tools = {}  # type: Dict[str, str]
    for item in items:
        if "=" not in item:
            raise ValueError(f"tool entry must be NAME=VALUE, got {item!r}")
        name, value = item.split("=", 1)
        tools[name] = value
    return tools


def _write_json(path: str, data: dict) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"  -> {out}")


def _parse_sim_results(run_dir: str, return_code: int = 0) -> Dict:
    """Extract cycle count, wall time, sim speed, outcome, and tohost from sim.log."""
    sim_log = Path(run_dir) / "sim.log"
    results = {}  # type: Dict
    if not sim_log.exists():
        results["outcome"] = f"ERROR_rc{return_code}" if return_code != 0 else "INCOMPLETE"
        return results
    text = sim_log.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Executed cycles:\s+(\d+)", text)
    if m:
        results["executed_cycles"] = int(m.group(1))
    m = re.search(r"Wallclock time:\s+([0-9.]+)\s*s", text)
    if m:
        results["wallclock_time_s"] = float(m.group(1))
    m = re.search(r"Simulation speed:\s+([0-9.]+)\s*cycles/s", text)
    if m:
        results["sim_speed_cycles_per_s"] = float(m.group(1))
    m = re.search(r"tohost = (\d+)", text)
    if m:
        results["tohost"] = int(m.group(1))
    if re.search(r"Core Test \*\*\* SUCCESS \*\*\*", text):
        results["outcome"] = "SUCCESS"
    elif re.search(r"Core Test \*\*\* FAIL", text):
        results["outcome"] = "FAILED"
    elif re.search(r"tohost = [1-9]", text):
        results["outcome"] = "FAILED"
    if "outcome" not in results:
        if return_code == 0:
            results["outcome"] = "INCOMPLETE"
        elif return_code == 141:
            results["outcome"] = "KILLED"
        elif return_code == 124:
            results["outcome"] = "TIMEOUT"
        else:
            results["outcome"] = f"ERROR_rc{return_code}"
    return results


def _sha256_file(path: str) -> Optional[str]:
    """Return hex SHA256 of a file, or None if it doesn't exist."""
    p = Path(path)
    if not p.exists():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot_hashes(inputs_dir: str, elf: str) -> Dict[str, Optional[str]]:
    """Hash key build inputs snapshotted into inputs_dir."""
    d = Path(inputs_dir)
    elf_name = Path(elf).name
    ll_files = sorted(d.glob("*.ll"))
    result = {"elf": _sha256_file(str(d / elf_name))}  # type: Dict[str, Optional[str]]
    for ll in ll_files:
        stem = ll.stem
        if stem.endswith("-compat"):
            result["compat_llvm_ir"] = _sha256_file(str(ll))
        else:
            result["llvm_ir"] = _sha256_file(str(ll))
    return result


def _write_repro_sh(run_dir: str, env_vars: List[str], make_command: str) -> str:
    """Write repro.sh with the exact commands needed to reproduce this sim run.

    Returns the path to the written script.
    """
    lines = [
        "#!/usr/bin/env bash",
        "# Reproduces this sim run from AZilla/tvm-apps/.",
        "# Paths are absolute to the machine where this run was recorded.",
        "set -e",
        "",
        "# Environment",
    ]
    for kv in env_vars:
        if "=" in kv:
            k, v = kv.split("=", 1)
            lines.append(f'export {k}="{v}"')
    lines.append("")
    lines.append("# Sim command")
    lines.append(make_command)
    lines.append("")

    out = Path(run_dir) / "repro.sh"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)
    print(f"  -> {out}")
    return str(out)


def _write_summary(run_dir: str, data: dict) -> None:
    """Write summary.txt with human-readable sim outcome after a run."""
    results = data.get("results", {})
    lines = [
        f"app:          {data.get('app', '')}",
        f"run_id:       {data.get('run_id', '')}",
        f"outcome:      {results.get('outcome', 'unknown')}",
        f"return_code:  {data.get('return_code', '')}",
        f"cycles:       {results.get('executed_cycles', 'n/a')}",
        f"wallclock:    {results.get('wallclock_time_s', 'n/a')} s",
        f"sim_speed:    {results.get('sim_speed_cycles_per_s', 'n/a')} cycles/s",
        f"tohost:       {results.get('tohost', 'n/a')}",
        f"elf_sha256:   {data.get('inputs_sha256', {}).get('elf', 'n/a')}",
        f"start:        {data.get('start_time', '')}",
        f"end:          {data.get('end_time', '')}",
        "",
    ]
    trace_log = Path(run_dir) / "trace_hart_00.log"
    if trace_log.exists():
        lines.append("--- last 10 trace lines ---")
        trace_lines = trace_log.read_text(encoding="utf-8", errors="replace").splitlines()
        lines.extend(trace_lines[-10:])
        lines.append("")

    out = Path(run_dir) / "summary.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  -> {out}")


def _collected_files(run_dir: str) -> List[str]:
    root = Path(run_dir)
    names = ["sim.log", "transcript", "sim.fst", "sim.vcd", "waveform.fsdb"]
    files = [root / name for name in names]
    files.extend(sorted(root.glob("trace_hart*.dasm")))
    files.extend(sorted(root.glob("trace_hart*.log")))
    files.extend(sorted(root.glob("trace_hart*_commit.log")))
    return [str(path.resolve()) for path in files if path.exists()]


def _build_stages(app: str, app_kind: str, args) -> List[Dict]:
    """Build the pipeline stage list from manifest args."""
    tvm_dir = _path(args.tvm_dir)
    ir_dir = _path(args.ir_dir)
    obj_dir = _path(args.obj_dir)
    bin_dir = _path(args.bin_dir)
    sim_dir = _path(args.sim_dir)

    codegen_ir_produces = []  # type: List[str]
    if app_kind == "kernel":
        codegen_ir_produces = [
            f"{ir_dir}/00_tir.py",
            f"{ir_dir}/03_codegen.ll",
            f"{ir_dir}/03_codegen.s",
        ]
    elif app_kind == "model":
        codegen_ir_produces = [
            f"{ir_dir}/00_exported_relax.py",
            f"{ir_dir}/01_after_dpl_pass.py",
            f"{ir_dir}/02_zero_pipeline.py",
            f"{ir_dir}/03_codegen.ll",
            f"{ir_dir}/03_codegen.s",
        ]

    codegen_consumes = []  # type: List[str]
    if getattr(args, "generator", ""):
        codegen_consumes.append(_path(args.generator))

    cross_consumes = [f"{tvm_dir}/{app}.ll"]
    if getattr(args, "main_c", ""):
        cross_consumes.append(_path(args.main_c))

    return [
        {
            "id": "codegen",
            "label": "TVM codegen",
            "tool": "TVM_PYTHON",
            "consumes": codegen_consumes,
            "produces": codegen_ir_produces + [
                f"{tvm_dir}/{app}.ll",
                f"{tvm_dir}/{app}.s",
            ],
            "next": "cross_compile",
            "notes": (
                "Runs kernel/model generator; emits LLVM IR and assembly "
                "to ir/ (numbered stage dumps) and tvm/ (final inputs for cross-compile)"
            ),
        },
        {
            "id": "cross_compile",
            "label": "Cross-compile (LLVM 22→20 compat + RISC-V object)",
            "tool": "RISCV_CC",
            "consumes": cross_consumes,
            "produces": [
                f"{obj_dir}/{app}-compat.ll",
                f"{obj_dir}/{app}.o",
                f"{obj_dir}/main.c.o",
            ],
            "next": "link",
            "notes": (
                "Strips nocreateundeforpoison attr (LLVM 22 vs riscv-clang 20 mismatch); "
                "cross-compiles LLVM IR and wrapper main.c to RISC-V object files"
            ),
        },
        {
            "id": "link",
            "label": "Link ELF",
            "tool": "RISCV_CC",
            "consumes": [
                f"{obj_dir}/{app}.o",
                f"{obj_dir}/main.c.o",
                _path(args.linker_script),
            ],
            "produces": [
                _path(args.elf),
                f"{bin_dir}/{app}.map",
                f"{bin_dir}/{app}.dump",
            ],
            "next": "sim",
            "notes": "Links with CRT/runtime; strips ELF in place; produces linker map and full disassembly dump",
        },
        {
            "id": "sim",
            "label": "Verilator sim",
            "tool": "VERILATOR_BINARY",
            "consumes": [_path(args.elf)],
            "produces": [
                f"{sim_dir}/runs/<RUN_ID>/sim.log",
                f"{sim_dir}/runs/<RUN_ID>/trace_hart_00.dasm",
                f"{sim_dir}/runs/<RUN_ID>/trace_hart_00.log",
                f"{sim_dir}/runs/<RUN_ID>/manifest.json",
            ],
            "next": None,
            "notes": (
                "Loads ELF into simulated AraXL RISC-V processor via -l ram,<elf>,elf; "
                "outputs cycle counts, hart traces, and per-run manifest"
            ),
        },
    ]


def _write_pipeline_json(
    output_path: str, app: str, app_kind: str, stages: List[Dict]
) -> None:
    """Write pipeline.json with a machine-readable stage graph."""
    data = {
        "app": app,
        "app_kind": app_kind,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "stages": stages,
    }
    _write_json(output_path, data)


def _write_readme(
    readme_path: str, app: str, app_kind: str, stages: List[Dict]
) -> None:
    """Write README.md with a human-readable explanation of the build tree."""
    now = datetime.datetime.now().isoformat(timespec="seconds")
    lines = [
        f"# {app} build tree",
        "",
        f"**App kind:** {app_kind}  ",
        f"**Generated:** {now}",
        "",
        "## Pipeline stages",
        "",
        "| Stage | Label | Tool |",
        "|-------|-------|------|",
    ]
    for s in stages:
        lines.append(f"| `{s['id']}` | {s['label']} | `{s['tool']}` |")
    lines.append("")

    for s in stages:
        lines.append(f"### `{s['id']}` — {s['label']}")
        lines.append("")
        lines.append(f"**Tool:** `{s['tool']}`")
        if s["consumes"]:
            lines.append("")
            lines.append("**Consumes:**")
            for c in s["consumes"]:
                lines.append(f"- `{c}`")
        if s["produces"]:
            lines.append("")
            lines.append("**Produces:**")
            for p in s["produces"]:
                lines.append(f"- `{p}`")
        lines.append("")
        if s.get("notes"):
            lines.append(f"*{s['notes']}*")
            lines.append("")
        next_id = s["next"]
        lines.append(f"**Next stage:** `{next_id}`" if next_id else "**Next stage:** *(end of pipeline)*")
        lines.append("")

    out = Path(readme_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  -> {out}")


def app_manifest(args: argparse.Namespace) -> int:
    app_dir = _path(args.app_dir)
    data = {
        "app": args.app,
        "app_kind": args.app_kind,
        "generator": _path(args.generator),
        "wrapper_main": _path(args.main_c),
        "kernel_deps": [_path(dep) for dep in args.kernel_dep],
        "pipeline": str(Path(app_dir) / "pipeline.json"),
        "target": {
            "mtriple": args.target_triple,
            "mattr": args.target_mattr.split(",") if args.target_mattr else [],
            "mabi": args.target_abi,
        },
        "configuration": {
            "config": args.config,
            "nr_clusters": int(args.nr_clusters),
            "nr_lanes": int(args.nr_lanes),
            "mem_latency": int(args.mem_latency),
            "cva6_latency": int(args.cva6_latency),
            "ring_latency": int(args.ring_latency),
            "trace": args.trace,
        },
        "tools": _tool_map(args.tool),
        "paths": {
            "app_dir": app_dir,
            "ir_dir": _path(args.ir_dir),
            "tvm_dir": _path(args.tvm_dir),
            "obj_dir": _path(args.obj_dir),
            "bin_dir": _path(args.bin_dir),
            "sim_dir": _path(args.sim_dir),
            "elf": _path(args.elf),
            "llvm_ir": _path(args.llvm_ir),
            "compat_llvm_ir": _path(args.compat_llvm_ir),
            "linker_script": _path(args.linker_script),
            "verilator_binary": _path(args.verilator_binary),
        },
    }
    _write_json(args.output, data)
    stages = _build_stages(args.app, args.app_kind, args)
    _write_pipeline_json(str(Path(app_dir) / "pipeline.json"), args.app, args.app_kind, stages)
    _write_readme(str(Path(app_dir) / "README.md"), args.app, args.app_kind, stages)
    return 0


def audit(args: argparse.Namespace) -> int:
    """Regenerate pipeline.json and README.md without touching manifest.json."""
    app_dir = _path(args.app_dir)
    stages = _build_stages(args.app, args.app_kind, args)
    _write_pipeline_json(str(Path(app_dir) / "pipeline.json"), args.app, args.app_kind, stages)
    _write_readme(str(Path(app_dir) / "README.md"), args.app, args.app_kind, stages)
    return 0


def sim_manifest(args: argparse.Namespace) -> int:
    rc = int(args.return_code)
    inputs_dir = getattr(args, "inputs_dir", "") or ""
    repro_env = list(getattr(args, "repro_env", None) or [])

    hashes = _snapshot_hashes(inputs_dir, args.elf) if inputs_dir else {}
    repro_path = _write_repro_sh(args.cwd, repro_env, args.command) if repro_env else ""

    data = {
        "app": args.app,
        "run_id": args.run_id,
        "simulator": args.simulator,
        "configuration": {
            "config": args.config,
            "nr_clusters": int(args.nr_clusters),
            "nr_lanes": int(args.nr_lanes),
            "mem_latency": int(args.mem_latency),
            "cva6_latency": int(args.cva6_latency),
            "ring_latency": int(args.ring_latency),
            "trace": args.trace,
        },
        "command": args.command,
        "cwd": _path(args.cwd),
        "elf": _path(args.elf),
        "verilator_binary": _path(args.verilator_binary),
        "return_code": rc,
        "start_time": args.start_time,
        "end_time": args.end_time,
        "inputs_dir": _path(inputs_dir) if inputs_dir else "",
        "inputs_sha256": hashes,
        "repro_sh": repro_path,
        "results": _parse_sim_results(args.cwd, rc),
        "collected_files": _collected_files(args.cwd),
    }
    _write_json(args.output, data)
    _write_summary(args.cwd, data)
    return 0


def env_snapshot(args: argparse.Namespace) -> int:
    """Write env.json with TVM version, git commit, tool paths, and timestamp."""
    import subprocess

    try:
        import tvm as _tvm
        tvm_version = _tvm.__version__
    except ImportError:
        tvm_version = "unknown"

    git_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
        cwd=args.git_dir,
    )
    git_commit = git_result.stdout.strip() if git_result.returncode == 0 else "unknown"

    data = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "git_commit": git_commit,
        "tools": {
            "RISCV_CC": args.riscv_cc,
        },
        "tvm_version": tvm_version,
    }
    _write_json(args.output, data)
    return 0


def report(args: argparse.Namespace) -> int:
    """Print a sim run summary to stdout."""
    run_dir = Path(_path(args.run_dir))
    manifest_path = run_dir / "manifest.json"
    summary_path = run_dir / "summary.txt"

    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        results = data.get("results", {})
        print(f"app:         {data.get('app', args.app)}")
        print(f"run_id:      {data.get('run_id', '')}")
        print(f"outcome:     {results.get('outcome', 'unknown')}")
        print(f"return_code: {data.get('return_code', '')}")
        print(f"cycles:      {results.get('executed_cycles', 'n/a')}")
        print(f"tohost:      {results.get('tohost', 'n/a')}")
        print(f"elf_sha256:  {data.get('inputs_sha256', {}).get('elf', 'n/a')}")
        print(f"start:       {data.get('start_time', '')}")
        print(f"end:         {data.get('end_time', '')}")
    else:
        print(f"ERROR: manifest not found at {manifest_path}")

    if summary_path.exists():
        print("")
        print("--- summary ---")
        print(summary_path.read_text(encoding="utf-8"))
    return 0


def _add_audit_args(p: argparse.ArgumentParser) -> None:
    """Add path/kind args shared by app-manifest and audit subparsers."""
    p.add_argument("--app", required=True)
    p.add_argument("--app-kind", required=True)
    p.add_argument("--generator", default="")
    p.add_argument("--main-c", default="")
    p.add_argument("--app-dir", required=True)
    p.add_argument("--ir-dir", required=True)
    p.add_argument("--tvm-dir", required=True)
    p.add_argument("--obj-dir", required=True)
    p.add_argument("--bin-dir", required=True)
    p.add_argument("--sim-dir", required=True)
    p.add_argument("--elf", required=True)
    p.add_argument("--llvm-ir", required=True)
    p.add_argument("--compat-llvm-ir", required=True)
    p.add_argument("--linker-script", required=True)
    p.add_argument("--verilator-binary", required=True)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    app = sub.add_parser("app-manifest", help="write build/<app>/manifest.json")
    app.add_argument("--output", required=True)
    _add_audit_args(app)
    app.add_argument("--kernel-dep", action="append", default=[])
    app.add_argument("--target-triple", required=True)
    app.add_argument("--target-mattr", required=True)
    app.add_argument("--target-abi", required=True)
    app.add_argument("--config", required=True)
    app.add_argument("--nr-clusters", required=True)
    app.add_argument("--nr-lanes", required=True)
    app.add_argument("--mem-latency", default="0")
    app.add_argument("--cva6-latency", default="0")
    app.add_argument("--ring-latency", default="0")
    app.add_argument("--trace", required=True)
    app.add_argument("--tool", action="append", default=[])
    app.set_defaults(func=app_manifest)

    aud = sub.add_parser("audit", help="regenerate build/<app>/pipeline.json and README.md")
    _add_audit_args(aud)
    aud.set_defaults(func=audit)

    sim = sub.add_parser("sim-manifest", help="write sim/runs/<run_id>/manifest.json")
    sim.add_argument("--output", required=True)
    sim.add_argument("--app", required=True)
    sim.add_argument("--run-id", required=True)
    sim.add_argument("--simulator", default="verilator")
    sim.add_argument("--command", required=True)
    sim.add_argument("--cwd", required=True)
    sim.add_argument("--elf", required=True)
    sim.add_argument("--verilator-binary", required=True)
    sim.add_argument("--return-code", required=True)
    sim.add_argument("--start-time", required=True)
    sim.add_argument("--end-time", required=True)
    sim.add_argument("--config", default="default")
    sim.add_argument("--nr-clusters", default="0")
    sim.add_argument("--nr-lanes", default="0")
    sim.add_argument("--mem-latency", default="0")
    sim.add_argument("--cva6-latency", default="0")
    sim.add_argument("--ring-latency", default="0")
    sim.add_argument("--trace", default="0")
    sim.add_argument("--inputs-dir", default="")
    sim.add_argument("--repro-env", action="append", default=[])
    sim.set_defaults(func=sim_manifest)

    env = sub.add_parser("env-snapshot", help="write bin/env.json with TVM version and git commit")
    env.add_argument("--output", required=True)
    env.add_argument("--riscv-cc", default="")
    env.add_argument("--git-dir", default=".")
    env.set_defaults(func=env_snapshot)

    rep = sub.add_parser("report", help="print sim run summary to stdout")
    rep.add_argument("--run-dir", required=True)
    rep.add_argument("--app", default="")
    rep.set_defaults(func=report)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
