#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════════
#  flow/scripts/run-sim.sh — shared, provider-agnostic RTL-sim runner
#
#  Runs a bare-metal ELF on the AraXL RTL simulator (Verilator or VCS) with the
#  full run-management UX: per-run dir + `latest` symlink, inputs/ snapshot, a
#  background live monitor, live spike-dasm instruction-trace decode, and
#  return-code propagation. It is COMPLETELY ELF-agnostic — it does not care how
#  the ELF was produced (C kernel, TVM, TileLang, prebuilt), which is what lets
#  every provider share one runner and one set of sim binaries.
#
#  This script intentionally does NOT emit manifest.json: that needs the TVM
#  conda env and lives in Make (sim-run.mk), which calls this script and then
#  reads the captured rc/start/end/cmd from the files written here:
#     <run-dir>/.sim_start  <run-dir>/.sim_end  <run-dir>/.sim_rc  <run-dir>/.sim_cmd
#
#  Exit code = the simulator's return code (so callers can gate on it).
# ════════════════════════════════════════════════════════════════════════════
set -uo pipefail

usage() {
    cat >&2 <<'EOF'
usage: run-sim.sh --ara-dir DIR --simulator (verilator|vcs) --elf PATH
                  --label NAME --run-dir DIR --sim-dir DIR --run-id ID
                  [hardware config + tool paths, see below]

required:
  --ara-dir DIR        repo root (git toplevel)
  --simulator NAME     verilator | vcs
  --elf PATH           ELF to load and run (any provider)
  --label NAME         app label for logs/manifest (e.g. c:fmatmul)
  --run-dir DIR        this run's output dir (…/03_sim/runs/<run-id>)
  --sim-dir DIR        parent sim dir (…/03_sim); 'latest' symlink lives here
  --run-id ID          run identifier

hardware config (for the log header + hardware make invocation):
  --config NAME --nr-clusters N --nr-lanes N
  --mem-latency N --cva6-latency N --ring-latency N
  --trace (0|1) --sim-cycle-arg STR

verilator backend:
  --veril-binary PATH
vcs backend:
  --vcs-binary PATH --vcs-dpi PATH --vcs-build-dir DIR
  --vcs-env STR            (env prefix string, may be empty)
  --return-status PATH     (hardware/scripts/return_status.sh)

tools (optional; degrade gracefully if absent):
  --spike-dasm PATH        live + final instruction-trace decode
  --monitor PATH           sim-monitor.sh

inputs snapshot (repeatable; missing files skipped):
  --snapshot PATH
EOF
    exit 2
}

# ── defaults ────────────────────────────────────────────────────────────────
ARA_DIR=""; SIMULATOR=""; ELF=""; LABEL=""; RUN_DIR=""; SIM_DIR=""; RUN_ID=""
CONFIG="default"; NRC="2"; NRL="4"; MEMLAT="0"; CVA6LAT="0"; RINGLAT="0"
TRACE="0"; SIM_CYCLE_ARG=""
VERIL_BINARY=""
VCS_BINARY=""; VCS_DPI=""; VCS_BUILD_DIR=""; VCS_ENV=""; RETURN_STATUS=""
SPIKE_DASM=""; MONITOR=""
SNAPSHOTS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ara-dir)       ARA_DIR="$2"; shift 2;;
        --simulator)     SIMULATOR="$2"; shift 2;;
        --elf)           ELF="$2"; shift 2;;
        --label)         LABEL="$2"; shift 2;;
        --run-dir)       RUN_DIR="$2"; shift 2;;
        --sim-dir)       SIM_DIR="$2"; shift 2;;
        --run-id)        RUN_ID="$2"; shift 2;;
        --config)        CONFIG="$2"; shift 2;;
        --nr-clusters)   NRC="$2"; shift 2;;
        --nr-lanes)      NRL="$2"; shift 2;;
        --mem-latency)   MEMLAT="$2"; shift 2;;
        --cva6-latency)  CVA6LAT="$2"; shift 2;;
        --ring-latency)  RINGLAT="$2"; shift 2;;
        --trace)         TRACE="$2"; shift 2;;
        --sim-cycle-arg) SIM_CYCLE_ARG="$2"; shift 2;;
        --veril-binary)  VERIL_BINARY="$2"; shift 2;;
        --vcs-binary)    VCS_BINARY="$2"; shift 2;;
        --vcs-dpi)       VCS_DPI="$2"; shift 2;;
        --vcs-build-dir) VCS_BUILD_DIR="$2"; shift 2;;
        --vcs-env)       VCS_ENV="$2"; shift 2;;
        --return-status) RETURN_STATUS="$2"; shift 2;;
        --spike-dasm)    SPIKE_DASM="$2"; shift 2;;
        --monitor)       MONITOR="$2"; shift 2;;
        --snapshot)      SNAPSHOTS+=("$2"); shift 2;;
        -h|--help)       usage;;
        *) echo "run-sim.sh: unknown option: $1" >&2; usage;;
    esac
done

for req in ARA_DIR SIMULATOR ELF LABEL RUN_DIR SIM_DIR RUN_ID; do
    if [[ -z "${!req}" ]]; then echo "run-sim.sh: missing --${req,,}" >&2; usage; fi
done

TRACE_ENABLED=""
case "$TRACE" in 1|true|yes|on) TRACE_ENABLED=1;; esac
trace_status=$([[ -n "$TRACE_ENABLED" ]] && echo 1 || echo 0)

APP_PATH="$(cd "$(dirname "$ELF")" && pwd)"
APP="$(basename "$ELF")"
RAW_DASM="$RUN_DIR/trace_hart_00.dasm"
SPIKE_DASM_LOG="$RUN_DIR/trace_hart_00.log"

mkdir -p "$RUN_DIR/inputs"
ln -sfn "runs/$RUN_ID" "$SIM_DIR/latest"

# Snapshot the listed reproducibility inputs (skip any that do not exist).
for f in "${SNAPSHOTS[@]:-}"; do
    [[ -n "$f" && -e "$f" ]] && cp "$f" "$RUN_DIR/inputs/" 2>/dev/null || true
done

start="$(date -Iseconds)"
echo "$start" > "$RUN_DIR/.sim_start"

# ── assemble the hardware make invocation (the actual simulator launch) ──────
# Path tokens are wrapped in escaped double-quotes inside $cmd so that, when the
# string is eval'd below, paths containing spaces survive intact.
if [[ "$SIMULATOR" == "verilator" ]]; then
    if [[ ! -f "$VERIL_BINARY" ]]; then
        echo "ERROR: Verilator binary not found at $VERIL_BINARY. Run 'make verilate' first." >&2
        echo 1 > "$RUN_DIR/.sim_rc"; echo "$(date -Iseconds)" > "$RUN_DIR/.sim_end"; exit 1
    fi
    VERIL_LIB="$(dirname "$VERIL_BINARY")/"
    cmd="make -C \"$ARA_DIR/hardware\" simv veril_library=\"$VERIL_LIB\" app_path=\"$APP_PATH\" app=\"$APP\" trace=$TRACE_ENABLED sim_run_dir=\"$RUN_DIR\" veril_run_args='$SIM_CYCLE_ARG'"
elif [[ "$SIMULATOR" == "vcs" ]]; then
    if [[ ! -f "$VCS_BINARY" ]]; then
        echo "ERROR: VCS binary not found at $VCS_BINARY. Run 'make compile-vcs' first." >&2
        echo 1 > "$RUN_DIR/.sim_rc"; echo "$(date -Iseconds)" > "$RUN_DIR/.sim_end"; exit 1
    fi
    # Stage the ELF in the (writable) run dir so elf2vmem writes the DRAM vmem
    # there, not next to a possibly read-only source ELF (e.g. prebuilt:).
    cp -f "$ELF" "$RUN_DIR/inputs/" 2>/dev/null || true
    cmd="${VCS_ENV}make -C \"$ARA_DIR/hardware\" simv_vcs buildpath=\"$VCS_BUILD_DIR\" simv_vcs_binary=\"$VCS_BINARY\" simv_vcs_dpi=\"$VCS_DPI\" app_path=\"$RUN_DIR/inputs\" app=\"$APP\" nr_lanes=$NRL nr_clusters=$NRC sim_run_dir=\"$RUN_DIR\""
else
    echo "run-sim.sh: unknown simulator '$SIMULATOR'" >&2; exit 2
fi
printf '%s\n' "$cmd" > "$RUN_DIR/.sim_cmd"

# ── start the background live monitor (optional) ─────────────────────────────
monitor_pid=""
if [[ -n "$MONITOR" && -f "$MONITOR" ]]; then
    bash "$MONITOR" "$RUN_DIR" --interval 5 >/dev/null 2>&1 &
    monitor_pid=$!
fi

# ── run the sim, teeing everything to sim.log ────────────────────────────────
{
    printf "=== sim app=%s nr_clusters=%s nr_lanes=%s mem_latency=%s cva6_latency=%s ring_latency=%s simulator=%s trace=%s run_id=%s %s ===\n" \
        "$LABEL" "$NRC" "$NRL" "$MEMLAT" "$CVA6LAT" "$RINGLAT" "$SIMULATOR" "$trace_status" "$RUN_ID" "$start"
    printf "cmd: %s\n" "$cmd"

    if [[ "$SIMULATOR" == "verilator" ]]; then
        # Live instruction-trace decode: tail the raw DASM into spike-dasm as it grows.
        dasm_tail_pid=""; dasm_filter_pid=""; dasm_fifo=""
        if [[ -n "$SPIKE_DASM" && -x "$SPIKE_DASM" ]]; then
            dasm_fifo="$RUN_DIR/.trace_hart_00.fifo"; rm -f "$dasm_fifo"
            if mkfifo "$dasm_fifo"; then
                printf "cmd: tail -n +1 -F %s | stdbuf -oL %s > %s &\n" "$RAW_DASM" "$SPIKE_DASM" "$SPIKE_DASM_LOG"
                stdbuf -oL "$SPIKE_DASM" < "$dasm_fifo" > "$SPIKE_DASM_LOG" & dasm_filter_pid=$!
                tail -n +1 -F "$RAW_DASM" > "$dasm_fifo" 2>/dev/null & dasm_tail_pid=$!
            else
                printf "WARNING: could not create DASM live FIFO at %s; skipping live spike-dasm\n" "$dasm_fifo"
            fi
        else
            printf "WARNING: spike-dasm not executable at %s; keeping raw DASM only\n" "$SPIKE_DASM"
        fi

        eval "$cmd"; sim_rc=$?

        [[ -n "$dasm_tail_pid" ]] && { kill "$dasm_tail_pid" 2>/dev/null || true; wait "$dasm_tail_pid" 2>/dev/null || true; }
        [[ -n "$dasm_filter_pid" ]] && { wait "$dasm_filter_pid" 2>/dev/null || true; }
        [[ -n "$dasm_fifo" ]] && rm -f "$dasm_fifo"

        # Final clean spike-dasm pass over the complete raw trace.
        if [[ -f "$RAW_DASM" ]]; then
            if [[ -n "$SPIKE_DASM" && -x "$SPIKE_DASM" ]]; then
                dasm_tmp="$SPIKE_DASM_LOG.tmp"
                printf "cmd: %s < %s > %s\n" "$SPIKE_DASM" "$RAW_DASM" "$SPIKE_DASM_LOG"
                if "$SPIKE_DASM" < "$RAW_DASM" > "$dasm_tmp"; then mv "$dasm_tmp" "$SPIKE_DASM_LOG";
                else rm -f "$dasm_tmp"; printf "WARNING: final spike-dasm pass failed for %s\n" "$RAW_DASM"; fi
            fi
        else
            printf "WARNING: raw hart trace not found at %s\n" "$RAW_DASM"
        fi
        exit "$sim_rc"
    else
        eval "$cmd"; exit $?
    fi
} 2>&1 | tee "$RUN_DIR/sim.log"
rc=${PIPESTATUS[0]}

# VCS: derive pass/fail from the tohost value in the log (Verilator already exits nonzero on fail).
if [[ "$SIMULATOR" == "vcs" && $rc -eq 0 && -n "$RETURN_STATUS" && -x "$RETURN_STATUS" ]]; then
    "$RETURN_STATUS" "$RUN_DIR/sim.log"; rc=$?
fi

# Stop the monitor.
if [[ -n "$monitor_pid" ]]; then kill "$monitor_pid" 2>/dev/null || true; wait "$monitor_pid" 2>/dev/null || true; fi

echo "$(date -Iseconds)" > "$RUN_DIR/.sim_end"
echo "$rc" > "$RUN_DIR/.sim_rc"
exit "$rc"
