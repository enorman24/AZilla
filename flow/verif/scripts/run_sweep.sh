#!/usr/bin/env bash
# run_sweep.sh - run a set of directed verification kernels through verify_one.py,
# at most JOBS Verilator sims concurrently (default 3, honoring the core ceiling).
# Each kernel writes only into its own isolated build dir (no shared mutable file).
#
# Usage:
#   run_sweep.sh [--groups "g1 g2 ..."] [--kernel path.c] [--failed-only]
#                [--jobs N] [--cycle-cap N] [--wall S]
#                [--nr-lanes N] [--nr-clusters N] [--ara-dir D]
set -uo pipefail

ARA="${ARA_DIR:-/mnt/ssd/enorman/AZilla}"
VERIF="$ARA/flow/verif"
JOBS=3
CYCLE_CAP=200000
WALL=350
NL=4
NC=4
GRPS=""
SINGLE=""
FAILED_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --groups) GRPS="$2"; shift 2;;
    --kernel) SINGLE="$2"; shift 2;;
    --failed-only) FAILED_ONLY=1; shift;;
    --jobs) JOBS="$2"; shift 2;;
    --cycle-cap) CYCLE_CAP="$2"; shift 2;;
    --wall) WALL="$2"; shift 2;;
    --nr-lanes) NL="$2"; shift 2;;
    --nr-clusters) NC="$2"; shift 2;;
    --ara-dir) ARA="$2"; shift 2;;
    *) echo "unknown arg $1"; exit 2;;
  esac
done

# ensure the per-config linker script exists (read-only shared input)
LD="$VERIF/build/lib/link-nc${NC}-l${NL}.ld"
if [[ ! -f "$LD" ]]; then
  mkdir -p "$VERIF/build/lib"
  cp "$ARA/apps/common/arch.link.ld" "$LD"
  bash "$ARA/apps/common/script/align_sections.sh" "$NL" "$NC" "$LD"
  echo "generated linker script $LD"
fi

# collect kernel list
KERNELS=()
if [[ -n "$SINGLE" ]]; then
  KERNELS+=("$SINGLE")
elif [[ "$FAILED_ONLY" == "1" ]]; then
  # re-run kernels whose last result was not PASS
  while IFS= read -r rj; do
    st=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('status',''))" "$rj" 2>/dev/null)
    if [[ "$st" != "PASS" && -n "$st" ]]; then
      k=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('kernel',''))" "$rj")
      [[ -n "$k" ]] && KERNELS+=("$ARA/$k")
    fi
  done < <(find "$VERIF/build" -name result.json 2>/dev/null)
else
  for g in $GRPS; do
    while IFS= read -r f; do KERNELS+=("$f"); done < <(find "$VERIF/kernels/$g" -name '*.c' 2>/dev/null | sort)
  done
fi

if [[ ${#KERNELS[@]} -eq 0 ]]; then echo "no kernels selected"; exit 0; fi
echo "running ${#KERNELS[@]} kernels, jobs=$JOBS, nc=$NC nl=$NL, cycle-cap=$CYCLE_CAP wall=$WALL"

run_one() {
  local k="$1" ara="$2" nl="$3" nc="$4" cc="$5" wall="$6"
  local name grp out
  name=$(basename "$k" .c); grp=$(basename "$(dirname "$k")")
  out="$ara/flow/verif/build/$grp/$name"; rm -rf "$out"
  python3 "$ara/flow/verif/scripts/verify_one.py" --kernel "$k" \
    --meta "${k%.c}.meta.json" --outdir "$out" \
    --ara-dir "$ara" --nr-lanes "$nl" --nr-clusters "$nc" \
    --cycle-cap "$cc" --wall "$wall" 2>&1 | tail -1
}
export -f run_one

printf '%s\n' "${KERNELS[@]}" | \
  xargs -P "$JOBS" -I{} bash -c 'run_one "$@"' _ {} "$ARA" "$NL" "$NC" "$CYCLE_CAP" "$WALL"
echo "sweep complete"
