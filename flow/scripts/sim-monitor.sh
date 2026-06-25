#!/usr/bin/env bash
# sim-monitor.sh — live monitor for a Verilator sim run directory
#
# Usage:
#   sim-monitor.sh WATCH_DIR [--interval N]
#
# Polls WATCH_DIR every INTERVAL seconds (default: 5) and appends a status
# block to WATCH_DIR/live.log.  Exits automatically when the sim finishes.
#
# Tracked metrics:
#   - elapsed wall time (from manifest.json start_time if available)
#   - trace_hart_00.dasm line count + lines/sec (instructions retired)
#   - last simulated cycle number (first field of last dasm line)
#   - [hw-cycles] counter from sim.log (Verilator's internal cycle counter)
#   - privilege mode of last instruction (M=boot, U=user/app code)
#   - first M→U privilege transition (signals app code reached)
#   - last decoded instruction from trace_hart_00.log
#   - stall warning if no dasm growth for >= STALL_THRESH seconds
#   - final Executed cycles / Wallclock time / Simulation speed from sim.log

set -uo pipefail

# ── argument parsing ────────────────────────────────────────────────────────
WATCH_DIR=""
INTERVAL=5
STALL_THRESH=30

while [[ $# -gt 0 ]]; do
    case "$1" in
        --interval|-i)
            INTERVAL="${2:?--interval requires a value}"
            shift 2
            ;;
        --stall-thresh)
            STALL_THRESH="${2:?--stall-thresh requires a value}"
            shift 2
            ;;
        -*)
            echo "unknown option: $1" >&2; exit 1
            ;;
        *)
            WATCH_DIR="$1"
            shift
            ;;
    esac
done

if [[ -z "$WATCH_DIR" ]]; then
    echo "usage: sim-monitor.sh WATCH_DIR [--interval N] [--stall-thresh N]" >&2
    exit 1
fi

# Resolve symlink so we always report and write to the real run directory
WATCH_DIR="$(realpath "$WATCH_DIR")"

if [[ ! -d "$WATCH_DIR" ]]; then
    echo "error: directory does not exist: $WATCH_DIR" >&2
    exit 1
fi

LIVE_LOG="$WATCH_DIR/live.log"
SIM_LOG="$WATCH_DIR/sim.log"
DASM="$WATCH_DIR/trace_hart_00.dasm"
DECODED="$WATCH_DIR/trace_hart_00.log"
MANIFEST="$WATCH_DIR/manifest.json"

# ── helpers ─────────────────────────────────────────────────────────────────
fmt_elapsed() {
    local s="$1"
    printf "%d:%02d:%02d" $(( s/3600 )) $(( (s%3600)/60 )) $(( s%60 ))
}

# ── determine start time ─────────────────────────────────────────────────────
start_ts=$(date +%s)
if [[ -f "$MANIFEST" ]]; then
    st=$(grep -o '"start_time": *"[^"]*"' "$MANIFEST" 2>/dev/null \
         | grep -o '[0-9T:+Z-]*$' || true)
    if [[ -n "$st" ]]; then
        parsed=$(date -d "$st" +%s 2>/dev/null || true)
        [[ -n "$parsed" ]] && start_ts="$parsed"
    fi
fi

# ── write header ─────────────────────────────────────────────────────────────
{
    echo "=== sim-monitor started $(date -Iseconds) ==="
    echo "dir      : $WATCH_DIR"
    echo "interval : ${INTERVAL}s   stall-threshold: ${STALL_THRESH}s"
    echo ""
} | tee "$LIVE_LOG"

# ── poll loop ────────────────────────────────────────────────────────────────
prev_dasm_lines=0
no_growth_polls=0

while true; do
    now=$(date +%s)
    elapsed=$(( now - start_ts ))
    elapsed_fmt=$(fmt_elapsed "$elapsed")

    # ── status ──────────────────────────────────────────────────────────────
    status="RUNNING"
    rc=""
    if [[ -f "$SIM_LOG" ]]; then
        grep -q "SUCCESS" "$SIM_LOG" 2>/dev/null && status="SUCCESS"
        # match explicit failure: FAIL keyword or non-zero tohost
        grep -qE "FAIL|tohost = [1-9]" "$SIM_LOG" 2>/dev/null && status="FAILED"
    fi
    # manifest is written after sim exits; presence of return_code is definitive
    if [[ -f "$MANIFEST" ]]; then
        rc=$(grep -o '"return_code": *-\?[0-9]*' "$MANIFEST" 2>/dev/null \
             | grep -o -- '-\?[0-9]*$' || true)
        if [[ -n "$rc" && "$rc" != "0" && "$status" = "RUNNING" ]]; then
            status="FAILED"
        fi
    fi

    # ── trace / dasm metrics ─────────────────────────────────────────────────
    dasm_lines=0
    last_cycle="n/a"
    last_addr="n/a"
    priv="n/a"
    mu_transition="not yet"

    if [[ -f "$DASM" ]]; then
        dasm_lines=$(wc -l < "$DASM" 2>/dev/null || echo 0)
        last_line=$(tail -1 "$DASM" 2>/dev/null || true)
        if [[ -n "$last_line" ]]; then
            last_cycle=$(echo "$last_line" | awk '{print $1}')
            last_addr=$(echo "$last_line"  | awk '{print $2}')
            priv=$(echo "$last_line"       | awk '{print $3}')
        fi
        mu_line=$(grep -n ' U ' "$DASM" 2>/dev/null | head -1 | cut -d: -f1 || true)
        [[ -n "$mu_line" ]] && mu_transition="dasm line $mu_line"
    fi

    delta=$(( dasm_lines - prev_dasm_lines ))
    # lines per second; bc for one decimal place
    lps=$(echo "scale=1; $delta / $INTERVAL" | bc 2>/dev/null || echo "$delta")

    # ── last decoded instruction ─────────────────────────────────────────────
    last_instr="n/a"
    if [[ -f "$DECODED" ]]; then
        last_instr=$(tail -1 "$DECODED" 2>/dev/null \
                     | sed 's/^[[:space:]]*//' | cut -c1-80 || true)
        [[ -z "$last_instr" ]] && last_instr="(empty)"
    fi

    # ── hw-cycles counter (Verilator internal) ───────────────────────────────
    hw_cycles="n/a"
    if [[ -f "$SIM_LOG" ]]; then
        hw_cycles=$(grep -o '\[hw-cycles\]: *[0-9]*' "$SIM_LOG" 2>/dev/null \
                    | tail -1 | grep -o '[0-9]*$' || true)
        [[ -z "$hw_cycles" ]] && hw_cycles="n/a"
    fi

    # ── final stats (populated only after sim exits) ─────────────────────────
    exec_cycles=""
    wall_time=""
    sim_speed=""
    if [[ -f "$SIM_LOG" ]]; then
        exec_cycles=$(grep -o 'Executed cycles: *[0-9 ]*' "$SIM_LOG" 2>/dev/null \
                      | tail -1 | sed 's/[[:space:]]*$//' || true)
        wall_time=$(grep -o 'Wallclock time: *[0-9.]* s' "$SIM_LOG" 2>/dev/null \
                    | tail -1 || true)
        sim_speed=$(grep -o 'Simulation speed: *[0-9. a-zA-Z/()]*' "$SIM_LOG" 2>/dev/null \
                    | tail -1 | sed 's/[[:space:]]*$//' || true)
    fi

    # ── stall detection ──────────────────────────────────────────────────────
    if [[ "$delta" -eq 0 && "$status" = "RUNNING" ]]; then
        no_growth_polls=$(( no_growth_polls + 1 ))
    else
        no_growth_polls=0
    fi
    stall_secs=$(( no_growth_polls * INTERVAL ))
    stall_warn=""
    [[ "$stall_secs" -ge "$STALL_THRESH" ]] \
        && stall_warn="  *** STALLED? no new dasm lines for ${stall_secs}s ***"

    # ── write poll block ─────────────────────────────────────────────────────
    {
        printf "[%s] elapsed=%s  status=%s" \
               "$(date +%H:%M:%S)" "$elapsed_fmt" "$status"
        [[ -n "$rc" ]] && printf "  rc=%s" "$rc"
        echo ""
        printf "  dasm lines  : %s  (+%s/s)\n"   "$dasm_lines"  "$lps"
        printf "  last cycle  : %s\n"             "$last_cycle"
        printf "  hw-cycles   : %s\n"             "$hw_cycles"
        printf "  privilege   : %s  (M->U at: %s)\n" "$priv" "$mu_transition"
        printf "  last addr   : %s\n"             "$last_addr"
        printf "  last instr  : %s\n"             "$last_instr"
        [[ -n "$stall_warn"   ]] && echo "$stall_warn"
        [[ -n "$exec_cycles"  ]] && printf "  %-20s\n" "$exec_cycles"
        [[ -n "$wall_time"    ]] && printf "  %-20s\n" "$wall_time"
        [[ -n "$sim_speed"    ]] && printf "  %-20s\n" "$sim_speed"
        echo ""
    } | tee -a "$LIVE_LOG"

    prev_dasm_lines="$dasm_lines"

    if [[ "$status" = "SUCCESS" || "$status" = "FAILED" ]]; then
        echo "MONITOR EXITING — simulation complete (status=$status)" \
            | tee -a "$LIVE_LOG"
        break
    fi

    sleep "$INTERVAL"
done
