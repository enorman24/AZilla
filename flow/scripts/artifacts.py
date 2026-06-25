"""Artifact manifest helpers for the AraXL TVM app Makefile."""

import argparse
import datetime
import hashlib
import json
import re
import stat
import subprocess
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
    # [hw-cycles] is printed by the testbench on BOTH simulators; it's the only
    # cycle count VCS emits (VCS never prints Verilator's "Executed cycles").
    hw = re.findall(r"\[hw-cycles\]:\s+(\d+)", text)
    if hw:
        results["hw_cycles"] = int(hw[-1])
    # Resolved cycle count for summary/report: prefer Verilator's executed-cycles
    # total, else fall back to the on-chip hw-cycles counter (so VCS isn't 'n/a').
    if "executed_cycles" in results:
        results["cycles"], results["cycles_source"] = results["executed_cycles"], "executed"
    elif "hw_cycles" in results:
        results["cycles"], results["cycles_source"] = results["hw_cycles"], "hw-cycles"
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


def _fmt_cycles(results: Dict) -> str:
    """Resolved cycle count + its source (executed vs hw-cycles), or n/a."""
    c = results.get("cycles")
    if c is None:
        return "n/a"
    src = results.get("cycles_source")
    return f"{c} ({src})" if src else str(c)


def _write_summary(run_dir: str, data: dict) -> None:
    """Write summary.txt with human-readable sim outcome after a run."""
    results = data.get("results", {})
    lines = [
        f"app:          {data.get('app', '')}",
        f"run_id:       {data.get('run_id', '')}",
        f"outcome:      {results.get('outcome', 'unknown')}",
        f"return_code:  {data.get('return_code', '')}",
        f"cycles:       {_fmt_cycles(results)}",
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
        print(f"cycles:      {_fmt_cycles(results)}")
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


# ── results ledger + status matrix ──────────────────────────────────────────
def _git_commit(path: str) -> str:
    """Short git commit at `path`, or "" if unavailable (3.6-safe subprocess)."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL)
        return out.decode("utf-8", "replace").strip()
    except Exception:
        return ""


def _ledger_record(m: Dict) -> Dict:
    """Flatten a sim manifest.json into one ledger row (everything to re-run)."""
    app = m.get("app", "")
    provider = app.split(":", 1)[0] if ":" in app else ""
    cfg = m.get("configuration", {})
    res = m.get("results", {})
    inh = m.get("inputs_sha256", {})
    elf = m.get("elf", "")
    git_commit = tvm_version = ""
    if elf:
        envp = Path(elf).parent / "env.json"
        if envp.exists():
            try:
                e = json.loads(envp.read_text(encoding="utf-8"))
                git_commit = e.get("git_commit", "")
                tvm_version = e.get("tvm_version", "")
            except Exception:
                pass
    # Capture the commit directly for providers without an env.json (c/prebuilt).
    if not git_commit and elf:
        git_commit = _git_commit(Path(elf).parent)
    return {
        "ts": (m.get("start_time") or "")[:16],
        "app": app, "provider": provider,
        "simulator": m.get("simulator", ""),
        "config": cfg.get("config", ""),
        "nr_clusters": cfg.get("nr_clusters"), "nr_lanes": cfg.get("nr_lanes"),
        "mem_lat": cfg.get("mem_latency"), "cva6_lat": cfg.get("cva6_latency"),
        "ring_lat": cfg.get("ring_latency"), "trace": cfg.get("trace"),
        "outcome": res.get("outcome", ""), "tohost": res.get("tohost"),
        "cycles": res.get("cycles"), "cycles_src": res.get("cycles_source", ""),
        # Both metrics kept separately so the table can show them in distinct
        # columns: hw_cycles = on-chip vector-busy counter (both sims print it);
        # executed_cycles = Verilator whole-program total (Verilator only).
        "hw_cycles": res.get("hw_cycles"), "executed_cycles": res.get("executed_cycles"),
        "elf_sha256": inh.get("elf", ""),
        "ir_sha256": inh.get("compat_llvm_ir") or inh.get("llvm_ir", ""),
        "git_commit": git_commit, "tvm_version": tvm_version,
        "run_id": m.get("run_id", ""), "command": m.get("command", ""),
        "repro_sh": m.get("repro_sh", ""),
    }


def _read_ledger(path: str) -> List[Dict]:
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


def ledger_append(args: argparse.Namespace) -> int:
    """Append one run (from its sim manifest.json) to the results ledger."""
    m = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    rec = _ledger_record(m)
    out = Path(args.ledger)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return 0


def _ledger_import(ledger_path: str, glob_pat: str):
    """Merge on-disk sim manifests into the ledger (dedup by app+run_id; never
    loses history). Re-derives results from each run's sim.log with the current
    parser. Returns (newly_added, total)."""
    import glob
    rows = {(r.get("app"), r.get("run_id")): r for r in _read_ledger(ledger_path)}
    added = 0
    for mp in sorted(glob.glob(glob_pat)):
        try:
            m = json.loads(Path(mp).read_text(encoding="utf-8"))
        except Exception:
            continue
        if "run_id" not in m or "simulator" not in m:
            continue
        run_dir = str(Path(mp).parent)
        if (Path(run_dir) / "sim.log").exists():
            m["results"] = _parse_sim_results(run_dir, m.get("return_code", 0))
        rec = _ledger_record(m)
        key = (rec["app"], rec["run_id"])
        if key not in rows:
            added += 1
        rows[key] = rec
    recs = sorted(rows.values(), key=lambda r: (r.get("ts", ""), r.get("run_id", "")))
    out = Path(ledger_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
    return added, len(recs)


def ledger_backfill(args: argparse.Namespace) -> int:
    """Import on-disk sim manifests into the ledger (CLI wrapper)."""
    added, total = _ledger_import(args.ledger, args.glob)
    print(f"ledger: {total} runs ({added} newly imported) -> {args.ledger}")
    return 0


def _catalog(ara_dir: str) -> List[str]:
    """Every runnable program, mirroring `make list-apps` exclusions."""
    import glob
    apps = []
    for p in glob.glob(f"{ara_dir}/apps/*/main.c"):
        n = Path(p).parent.name
        if n != "benchmarks":
            apps.append(f"c:{n}")
    for base in ("kernels", "models"):
        for d in glob.glob(f"{ara_dir}/tvm-apps/{base}/*/"):
            n = Path(d).name
            if n == "common":
                continue
            if (Path(d) / f"{n}.py").exists():
                apps.append(f"tvm:{n}")
    for d in glob.glob(f"{ara_dir}/tilelang-apps/*/"):
        apps.append(f"tilelang:{Path(d).name}")
    return sorted(set(apps))


# Plain ASCII status words — emoji are double-width and break monospace alignment.
_OUTCOME_WORD = {"SUCCESS": "PASS", "FAILED": "FAIL", "INCOMPLETE": "incomplete"}


def _render_table(cols: List[str], rows: List[List[str]]) -> str:
    """A monospace-aligned Markdown pipe table (every column padded to its width)."""
    widths = [len(c) for c in cols]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    def fmt(cells):
        return "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells)) + " |"
    sep = "|" + "|".join("-" * (w + 2) for w in widths) + "|"
    return "\n".join([fmt(cols), sep] + [fmt(r) for r in rows]) + "\n"


def status(args: argparse.Namespace) -> int:
    """Render the latest-run-per-full-hardware-config results matrix to RESULTS.md
    + stdout. Always re-imports on-disk run manifests first (so it's up to date)."""
    if getattr(args, "backfill_glob", ""):
        added, total = _ledger_import(args.ledger, args.backfill_glob)
        print(f"ledger: {total} runs ({added} newly imported)")

    rows = _read_ledger(args.ledger)
    # Latest run per FULL hardware config — every knob is part of the identity, so
    # the same kernel at different clusters / lanes / latencies / trace / simulator
    # each gets its own row (rather than collapsing to one "latest").
    def geom_key(r):
        return (r.get("app"), r.get("simulator"), r.get("config"),
                r.get("nr_clusters"), r.get("nr_lanes"),
                r.get("mem_lat"), r.get("cva6_lat"), r.get("ring_lat"), r.get("trace"))
    latest = {}  # type: Dict
    for r in rows:
        key = geom_key(r)
        cur = latest.get(key)
        if cur is None or (r.get("ts", ""), r.get("run_id", "")) >= (cur.get("ts", ""), cur.get("run_id", "")):
            latest[key] = r
    by_app = {}  # type: Dict
    for r in latest.values():
        by_app.setdefault(r.get("app"), []).append(r)

    def _load_json(path):
        if path and Path(path).exists():
            try:
                return json.loads(Path(path).read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}
    notes = _load_json(args.notes)
    # Static per-program identity (what it computes / size / how many runs), keyed
    # by program id — declared, not derived (some sizes aren't in def_args).
    meta = _load_json(getattr(args, "meta", ""))

    catalog = _catalog(args.ara_dir) if args.ara_dir else sorted(by_app)
    for a in by_app:
        if a not in catalog:
            catalog.append(a)
    catalog = sorted(set(catalog))

    def s(v):
        return "-" if v is None or v == "" else str(v)

    def vec_cell(r):
        # On-chip vector-busy cycles (both sims print [hw-cycles]); 0 = no vector work.
        h = r.get("hw_cycles")
        if h is None:
            return "-"
        return "0 (no-vec)" if h == 0 else str(h)

    def tohost_cell(v):
        # Fail sentinel (2^63-1) is 19 digits and bloats the column; Result already says FAIL.
        return "FAIL" if str(v) in ("9223372036854775807", "0x7fffffffffffffff") else s(v)

    # Columns: static identity (Computes/Size/Runs, from meta.json) + every run knob
    # + the two cycle metrics in distinct columns (never conflated).
    cols = ["Program", "Computes", "Size", "Runs", "Result", "Sim", "config",
            "nc", "nl", "mem", "cva6", "ring", "trace",
            "Vec-cyc(hw)", "Whole-prog", "tohost", "Date", "Run id", "Notes"]
    trows = []  # type: List[List[str]]
    for app in catalog:
        m = meta.get(app, {})
        ident = [app, s(m.get("computes")), s(m.get("size")), s(m.get("runs"))]
        note = notes.get(app, "")
        # Cap the free-text Notes column so an over-long note can't blow out the
        # monospace table width and wrap every row (full detail lives in flow/docs/,
        # e.g. BROKEN_PROGRAMS_DIAGNOSIS.md). ASCII "..." keeps single-width alignment.
        if len(note) > 60:
            note = note[:57].rstrip() + "..."
        recs = sorted(by_app.get(app, []), key=lambda r: (
            s(r.get("simulator")), s(r.get("config")),
            r.get("nr_clusters") or 0, r.get("nr_lanes") or 0,
            r.get("mem_lat") or 0, r.get("cva6_lat") or 0, r.get("ring_lat") or 0, s(r.get("trace"))))
        if not recs:
            trows.append(ident + ["untested"] + ["-"] * 13 + [note])
            continue
        for r in recs:
            res = _OUTCOME_WORD.get(r.get("outcome", ""), r.get("outcome") or "?")
            date = (r.get("ts") or "")[:10] or "-"
            trows.append(ident + [
                res, s(r.get("simulator")), s(r.get("config")),
                s(r.get("nr_clusters")), s(r.get("nr_lanes")),
                s(r.get("mem_lat")), s(r.get("cva6_lat")), s(r.get("ring_lat")),
                s(r.get("trace")), vec_cell(r), s(r.get("executed_cycles")),
                tohost_cell(r.get("tohost")), date, s(r.get("run_id")), note,
            ])

    # Drop latency columns left at default (0/-) for every row: they remain part of
    # row identity (kept when any row is non-default) but are pure width when all zero.
    for _name in ("ring", "cva6", "mem"):
        _i = cols.index(_name)
        if all(row[_i] in ("0", "-") for row in trows):
            del cols[_i]
            for _row in trows:
                del _row[_i]

    npass = sum(1 for r in latest.values() if r.get("outcome") == "SUCCESS")
    hdr = (
        "# AraXL flow — program results\n\n"
        "_Auto-generated by `make status` (re-imports all on-disk runs, then renders). "
        "Do not edit by hand — put known-issue notes in `flow/results/notes.json`. "
        "One row = the **latest** run for a full hardware config: every knob "
        "(sim, config, nc=nr_clusters, nl=nr_lanes, mem/cva6/ring latency, trace) is "
        "part of the row identity, so the same program at different settings shows "
        "separately (mem/cva6/ring latency columns are hidden when every row is at the "
        "default 0, and reappear if any row is non-default). Never-run programs are "
        "`untested`. Re-run a row exactly via its "
        "run's `repro.sh` (by Run id); a differing `elf_sha256` (in the ledger) means "
        "the source changed._\n\n"
        "_Computes/Size/Runs come from `flow/results/meta.json` (declared per program — "
        "they explain why cycle counts differ: different problem size and number of "
        "kernel invocations). The two cycle columns are distinct metrics, never "
        "compared: **Vec-cyc(hw)** = on-chip vector-busy cycles (cumulative across the "
        "run's kernel calls; `0 (no-vec)` = pure-scalar); **Whole-prog** = Verilator's "
        "whole-program total (includes boot + scalar refs + printf-over-serial)._\n\n"
        + "```\n" + _render_table(cols, trows) + "```\n\n"
        + "_{} result(s) across {} program(s); {} passing._\n".format(len(latest), len(catalog), npass)
    )
    if args.out:
        Path(args.out).write_text(hdr, encoding="utf-8")
    print(hdr)
    if args.out:
        print("Wrote " + args.out)
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

    la = sub.add_parser("ledger-append", help="append one run to results/ledger.jsonl")
    la.add_argument("--manifest", required=True)
    la.add_argument("--ledger", required=True)
    la.set_defaults(func=ledger_append)

    lb = sub.add_parser("ledger-backfill", help="import on-disk sim manifests into the ledger (merge)")
    lb.add_argument("--glob", required=True)
    lb.add_argument("--ledger", required=True)
    lb.set_defaults(func=ledger_backfill)

    st = sub.add_parser("status", help="render the latest-per-(app,sim,config) results matrix")
    st.add_argument("--ledger", required=True)
    st.add_argument("--ara-dir", default="")
    st.add_argument("--notes", default="")
    st.add_argument("--meta", default="", help="per-program identity sidecar (computes/size/runs)")
    st.add_argument("--out", default="")
    st.add_argument("--backfill-glob", default="", help="import matching on-disk manifests before rendering")
    st.set_defaults(func=status)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
