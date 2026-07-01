#!/usr/bin/env python3
"""
Instruction inventory for the AZilla RVV 1.0 + RV64 ground-up verification suite.

This is the SPINE of the whole effort (Step 1). It is authored from the ISA
specifications (riscv-v-spec-1.0.pdf, riscv-unprivileged-isa-manual.pdf), NOT
from any repo documentation. Each entry is one base instruction mnemonic; the
per-(SEW,LMUL,mask,edge) variants are expanded at test-generation time.

The `expected` field is the prediction derived from reading the AraXL RTL
decoder/execute units in Step 0 reconnaissance (ara_pkg.sv op enum +
ara_dispatcher.sv). It is a PREDICTION used to sanity-check classification, not
an assertion of truth; the simulation result is what actually decides PASS /
FAIL / BLOCKED. Values:
  supported       - decoded + executed by AraXL; expect PASS
  blocked_illegal - not in the op enum; dispatcher raises illegal -> trap
  blocked_silent  - not decoded but does NOT trap; silently mis-decoded
                    (segment ld/st) -> expect FAIL-incorrect vs Spike oracle
  absent_ext      - scalar extension not present in this CVA6 config; the
                    instruction is not emitted by the toolchain and would trap.
                    Out of scope as "prove it works" (nothing to verify); kept
                    for coverage accounting + optional negative (trap) probes.

Run:  python3 inventory.py            # writes inventory.json/.csv/.md here
"""

import csv
import json
import os

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
INT_SEW = [8, 16, 32, 64]          # AraXL ELEN=64, SEW in {8,16,32,64}
FP_SEW = [16, 32, 64]              # FP requires SEW>=16 (no FP8); zvfh gives FP16
WIDEN_SEW = [8, 16, 32]            # source SEW for widening (dest is 2*SEW<=64)
NARROW_SEW = [16, 32, 64]          # dest SEW for narrowing reads 2*SEW source
NO_SEW = []                        # scalar / not SEW-parametric

_entries = []


def add(mnem, ext, group, fmt, forms, sew, expected, note=""):
    """forms: list of operand-form suffixes actually assembled (vv/vx/vi/...)."""
    _entries.append({
        "mnemonic": mnem,
        "ext": ext,                # "RVV" | "RV64"
        "group": group,
        "format": fmt,             # encoding group / scalar type
        "forms": forms,            # operand variants
        "sew": sew,                # applicable SEW set ([] if N/A)
        "expected": expected,
        "note": note,
    })


# ===========================================================================
# RVV 1.0
# ===========================================================================

# --- configuration ---------------------------------------------------------
add("vsetvli",  "RVV", "rvv-config", "vsetvli",  ["x"], NO_SEW, "supported", "sets vl/vtype; exercised by every vector kernel")
add("vsetivli", "RVV", "rvv-config", "vsetivli", ["x"], NO_SEW, "supported", "immediate AVL form")
add("vsetvl",   "RVV", "rvv-config", "vsetvl",   ["x"], NO_SEW, "supported", "register vtype form")

# --- unit-stride load/store ------------------------------------------------
for e in INT_SEW:
    add(f"vle{e}.v",  "RVV", "rvv-mem-unit", "VL-unit",  ["v"], [e], "supported", "unit-stride load (extraction primitive: verify early)")
    add(f"vse{e}.v",  "RVV", "rvv-mem-unit", "VS-unit",  ["v"], [e], "supported", "unit-stride store (extraction primitive: verify early)")
add("vlm.v", "RVV", "rvv-mem-unit", "VL-mask", ["v"], [8], "supported", "mask load EEW=1 (ceil(vl/8) bytes)")
add("vsm.v", "RVV", "rvv-mem-unit", "VS-mask", ["v"], [8], "supported", "mask store EEW=1")
for e in INT_SEW:
    add(f"vle{e}ff.v", "RVV", "rvv-mem-unit", "VL-ff", ["v"], [e], "blocked_illegal", "fault-only-first load: dispatcher raises illegal (TODO not implemented)")

# --- strided load/store ----------------------------------------------------
for e in INT_SEW:
    add(f"vlse{e}.v", "RVV", "rvv-mem-strided", "VL-strided", ["v"], [e], "supported", "strided load")
    add(f"vsse{e}.v", "RVV", "rvv-mem-strided", "VS-strided", ["v"], [e], "supported", "strided store")

# --- indexed load/store (unordered + ordered) ------------------------------
for e in INT_SEW:
    add(f"vluxei{e}.v", "RVV", "rvv-mem-indexed", "VL-idx-uo", ["v"], [e], "supported", "indexed-unordered (gather) load")
    add(f"vloxei{e}.v", "RVV", "rvv-mem-indexed", "VL-idx-o",  ["v"], [e], "supported", "indexed-ordered (gather) load")
    add(f"vsuxei{e}.v", "RVV", "rvv-mem-indexed", "VS-idx-uo", ["v"], [e], "supported", "indexed-unordered (scatter) store")
    add(f"vsoxei{e}.v", "RVV", "rvv-mem-indexed", "VS-idx-o",  ["v"], [e], "supported", "indexed-ordered (scatter) store")

# --- whole-register load/store --------------------------------------------
for nr in [1, 2, 4, 8]:
    add(f"vl{nr}re8.v",  "RVV", "rvv-mem-whole", "VL-whole", ["v"], [8],  "supported", f"whole-register load, {nr} reg(s)")
    add(f"vl{nr}re64.v", "RVV", "rvv-mem-whole", "VL-whole", ["v"], [64], "supported", f"whole-register load EEW64, {nr} reg(s)")
    add(f"vs{nr}r.v",    "RVV", "rvv-mem-whole", "VS-whole", ["v"], [8],  "supported", f"whole-register store, {nr} reg(s)")

# --- segment load/store (nf=2..8) -> silent mis-decode on AraXL ------------
# AraXL does not decode the nf field outside the whole-register path, so segment
# ops are silently treated as their non-segment counterpart (no trap) EXCEPT the
# fault-only-first segment load, whose ff lumop traps illegal like plain vle*ff.
for nf in [2, 4, 8]:
    add(f"vlseg{nf}e32.v",   "RVV", "rvv-mem-segment", "VL-seg",        ["v"], [32], "blocked_silent", "unit-stride segment load: nf not decoded -> silently treated as non-segment")
    add(f"vsseg{nf}e32.v",   "RVV", "rvv-mem-segment", "VS-seg",        ["v"], [32], "blocked_silent", "unit-stride segment store: silent mis-decode")
    add(f"vlsseg{nf}e32.v",  "RVV", "rvv-mem-segment", "VL-seg-strd",   ["v"], [32], "blocked_silent", "strided segment load: silent mis-decode")
    add(f"vssseg{nf}e32.v",  "RVV", "rvv-mem-segment", "VS-seg-strd",   ["v"], [32], "blocked_silent", "strided segment store: silent mis-decode")
    add(f"vluxseg{nf}ei32.v", "RVV", "rvv-mem-segment", "VL-seg-idx-uo", ["v"], [32], "blocked_silent", "indexed-unordered segment load: silent mis-decode")
    add(f"vloxseg{nf}ei32.v", "RVV", "rvv-mem-segment", "VL-seg-idx-o",  ["v"], [32], "blocked_silent", "indexed-ordered segment load: silent mis-decode")
    add(f"vsuxseg{nf}ei32.v", "RVV", "rvv-mem-segment", "VS-seg-idx-uo", ["v"], [32], "blocked_silent", "indexed-unordered segment store: silent mis-decode")
    add(f"vsoxseg{nf}ei32.v", "RVV", "rvv-mem-segment", "VS-seg-idx-o",  ["v"], [32], "blocked_silent", "indexed-ordered segment store: silent mis-decode")
    add(f"vlseg{nf}e32ff.v", "RVV", "rvv-mem-segment", "VL-seg-ff",     ["v"], [32], "blocked_illegal", "fault-only-first segment load: ff lumop traps illegal regardless of nf")

# --- integer arithmetic (OPIVV/OPIVX/OPIVI) --------------------------------
add("vadd",  "RVV", "rvv-int-arith", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported")
add("vsub",  "RVV", "rvv-int-arith", "OPIVV/VX",    ["vv", "vx"],       INT_SEW, "supported")
add("vrsub", "RVV", "rvv-int-arith", "OPIVX/VI",    ["vx", "vi"],       INT_SEW, "supported", "reverse subtract")
add("vand",  "RVV", "rvv-int-logical", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported")
add("vor",   "RVV", "rvv-int-logical", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported")
add("vxor",  "RVV", "rvv-int-logical", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported")
add("vsll",  "RVV", "rvv-int-shift", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported")
add("vsrl",  "RVV", "rvv-int-shift", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported")
add("vsra",  "RVV", "rvv-int-shift", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported")
add("vnsrl", "RVV", "rvv-int-narrow", "OPIVV/VX/VI", ["wv", "wx", "wi"], NARROW_SEW, "supported", "narrowing logical shift right")
add("vnsra", "RVV", "rvv-int-narrow", "OPIVV/VX/VI", ["wv", "wx", "wi"], NARROW_SEW, "supported", "narrowing arithmetic shift right")
add("vminu", "RVV", "rvv-int-minmax", "OPIVV/VX", ["vv", "vx"], INT_SEW, "supported")
add("vmin",  "RVV", "rvv-int-minmax", "OPIVV/VX", ["vv", "vx"], INT_SEW, "supported")
add("vmaxu", "RVV", "rvv-int-minmax", "OPIVV/VX", ["vv", "vx"], INT_SEW, "supported")
add("vmax",  "RVV", "rvv-int-minmax", "OPIVV/VX", ["vv", "vx"], INT_SEW, "supported")

# integer compares -> mask
add("vmseq",  "RVV", "rvv-int-cmp", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported")
add("vmsne",  "RVV", "rvv-int-cmp", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported")
add("vmsltu", "RVV", "rvv-int-cmp", "OPIVV/VX",    ["vv", "vx"],       INT_SEW, "supported")
add("vmslt",  "RVV", "rvv-int-cmp", "OPIVV/VX",    ["vv", "vx"],       INT_SEW, "supported")
add("vmsleu", "RVV", "rvv-int-cmp", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported")
add("vmsle",  "RVV", "rvv-int-cmp", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported")
add("vmsgtu", "RVV", "rvv-int-cmp", "OPIVX/VI",    ["vx", "vi"],       INT_SEW, "supported")
add("vmsgt",  "RVV", "rvv-int-cmp", "OPIVX/VI",    ["vx", "vi"],       INT_SEW, "supported")

# merge / move / carry
add("vmerge", "RVV", "rvv-int-merge", "OPIVV/VX/VI", ["vvm", "vxm", "vim"], INT_SEW, "supported", "mask-driven merge")
add("vmv.v",  "RVV", "rvv-int-merge", "OPIVV/VX/VI", ["v", "x", "i"],       INT_SEW, "supported", "vmv.v.v/.v.x/.v.i splat/copy")
add("vadc",   "RVV", "rvv-int-carry", "OPIVV/VX/VI", ["vvm", "vxm", "vim"], INT_SEW, "supported", "add-with-carry")
add("vsbc",   "RVV", "rvv-int-carry", "OPIVV/VX",    ["vvm", "vxm"],        INT_SEW, "supported", "subtract-with-borrow")
add("vmadc",  "RVV", "rvv-int-carry", "OPIVV/VX/VI", ["vvm", "vxm", "vim", "vv", "vx", "vi"], INT_SEW, "supported", "produce carry-out mask")
add("vmsbc",  "RVV", "rvv-int-carry", "OPIVV/VX",    ["vvm", "vxm", "vv", "vx"], INT_SEW, "supported", "produce borrow-out mask")

# extension
add("vzext", "RVV", "rvv-int-ext", "OPMVV-VXUNARY0", ["vf2", "vf4", "vf8"], [16, 32, 64], "supported", "zero-extend vf2/vf4/vf8")
add("vsext", "RVV", "rvv-int-ext", "OPMVV-VXUNARY0", ["vf2", "vf4", "vf8"], [16, 32, 64], "supported", "sign-extend vf2/vf4/vf8")

# --- integer mul / div / mul-add (OPMVV/OPMVX) -----------------------------
add("vmul",    "RVV", "rvv-int-mul", "OPMVV/VX", ["vv", "vx"], INT_SEW, "supported")
add("vmulh",   "RVV", "rvv-int-mul", "OPMVV/VX", ["vv", "vx"], INT_SEW, "supported", "high bits, signed")
add("vmulhu",  "RVV", "rvv-int-mul", "OPMVV/VX", ["vv", "vx"], INT_SEW, "supported", "high bits, unsigned")
add("vmulhsu", "RVV", "rvv-int-mul", "OPMVV/VX", ["vv", "vx"], INT_SEW, "supported", "high bits, signed*unsigned")
add("vdivu",   "RVV", "rvv-int-div", "OPMVV/VX", ["vv", "vx"], INT_SEW, "supported")
add("vdiv",    "RVV", "rvv-int-div", "OPMVV/VX", ["vv", "vx"], INT_SEW, "supported")
add("vremu",   "RVV", "rvv-int-div", "OPMVV/VX", ["vv", "vx"], INT_SEW, "supported")
add("vrem",    "RVV", "rvv-int-div", "OPMVV/VX", ["vv", "vx"], INT_SEW, "supported")
add("vmacc",   "RVV", "rvv-int-muladd", "OPMVV/VX", ["vv", "vx"], INT_SEW, "supported")
add("vnmsac",  "RVV", "rvv-int-muladd", "OPMVV/VX", ["vv", "vx"], INT_SEW, "supported")
add("vmadd",   "RVV", "rvv-int-muladd", "OPMVV/VX", ["vv", "vx"], INT_SEW, "supported")
add("vnmsub",  "RVV", "rvv-int-muladd", "OPMVV/VX", ["vv", "vx"], INT_SEW, "supported")

# widening integer
add("vwmul",    "RVV", "rvv-int-widen", "OPMVV/VX", ["vv", "vx"], WIDEN_SEW, "supported")
add("vwmulu",   "RVV", "rvv-int-widen", "OPMVV/VX", ["vv", "vx"], WIDEN_SEW, "supported")
add("vwmulsu",  "RVV", "rvv-int-widen", "OPMVV/VX", ["vv", "vx"], WIDEN_SEW, "supported")
add("vwmacc",   "RVV", "rvv-int-widen", "OPMVV/VX", ["vv", "vx"], WIDEN_SEW, "supported")
add("vwmaccu",  "RVV", "rvv-int-widen", "OPMVV/VX", ["vv", "vx"], WIDEN_SEW, "supported")
add("vwmaccsu", "RVV", "rvv-int-widen", "OPMVV/VX", ["vv", "vx"], WIDEN_SEW, "supported")
add("vwmaccus", "RVV", "rvv-int-widen", "OPMVX",    ["vx"],       WIDEN_SEW, "supported")
add("vwaddu",   "RVV", "rvv-int-widen", "OPMVV/VX", ["vv", "vx", "wv", "wx"], WIDEN_SEW, "supported")
add("vwadd",    "RVV", "rvv-int-widen", "OPMVV/VX", ["vv", "vx", "wv", "wx"], WIDEN_SEW, "supported")
add("vwsubu",   "RVV", "rvv-int-widen", "OPMVV/VX", ["vv", "vx", "wv", "wx"], WIDEN_SEW, "supported")
add("vwsub",    "RVV", "rvv-int-widen", "OPMVV/VX", ["vv", "vx", "wv", "wx"], WIDEN_SEW, "supported")

# --- fixed-point saturating / rounding (OPIVV/VX/VI + OPMVV averaging) ------
add("vsaddu",  "RVV", "rvv-fixed", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported", "saturating add unsigned")
add("vsadd",   "RVV", "rvv-fixed", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported", "saturating add signed")
add("vssubu",  "RVV", "rvv-fixed", "OPIVV/VX",    ["vv", "vx"],       INT_SEW, "supported")
add("vssub",   "RVV", "rvv-fixed", "OPIVV/VX",    ["vv", "vx"],       INT_SEW, "supported")
add("vaaddu",  "RVV", "rvv-fixed", "OPMVV/VX",    ["vv", "vx"],       INT_SEW, "supported", "averaging add unsigned (rounding via vxrm)")
add("vaadd",   "RVV", "rvv-fixed", "OPMVV/VX",    ["vv", "vx"],       INT_SEW, "supported")
add("vasubu",  "RVV", "rvv-fixed", "OPMVV/VX",    ["vv", "vx"],       INT_SEW, "supported")
add("vasub",   "RVV", "rvv-fixed", "OPMVV/VX",    ["vv", "vx"],       INT_SEW, "supported")
add("vsmul",   "RVV", "rvv-fixed", "OPIVV/VX",    ["vv", "vx"],       INT_SEW, "supported", "fractional mul with rounding+saturate")
add("vssrl",   "RVV", "rvv-fixed", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported", "scaling shift right logical (rounding)")
add("vssra",   "RVV", "rvv-fixed", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "supported", "scaling shift right arithmetic")
add("vnclipu", "RVV", "rvv-fixed", "OPIVV/VX/VI", ["wv", "wx", "wi"], NARROW_SEW, "supported", "narrowing clip unsigned")
add("vnclip",  "RVV", "rvv-fixed", "OPIVV/VX/VI", ["wv", "wx", "wi"], NARROW_SEW, "supported", "narrowing clip signed")

# --- floating-point (OPFVV/OPFVF) ------------------------------------------
add("vfadd",   "RVV", "rvv-fp-arith", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfsub",   "RVV", "rvv-fp-arith", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfrsub",  "RVV", "rvv-fp-arith", "OPFVF",    ["vf"],       FP_SEW, "supported")
add("vfmul",   "RVV", "rvv-fp-arith", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfdiv",   "RVV", "rvv-fp-arith", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfrdiv",  "RVV", "rvv-fp-arith", "OPFVF",    ["vf"],       FP_SEW, "supported")
add("vfmacc",  "RVV", "rvv-fp-muladd", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported", "FMA: oracle must be Spike (fusion)")
add("vfnmacc", "RVV", "rvv-fp-muladd", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfmsac",  "RVV", "rvv-fp-muladd", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfnmsac", "RVV", "rvv-fp-muladd", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfmadd",  "RVV", "rvv-fp-muladd", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfnmadd", "RVV", "rvv-fp-muladd", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfmsub",  "RVV", "rvv-fp-muladd", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfnmsub", "RVV", "rvv-fp-muladd", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfsqrt",  "RVV", "rvv-fp-unary", "OPFVV-VFUNARY1", ["v"], FP_SEW, "supported")
add("vfrsqrt7","RVV", "rvv-fp-unary", "OPFVV-VFUNARY1", ["v"], FP_SEW, "supported", "7-bit approx; oracle MUST be Spike")
add("vfrec7",  "RVV", "rvv-fp-unary", "OPFVV-VFUNARY1", ["v"], FP_SEW, "supported", "7-bit approx; oracle MUST be Spike")
add("vfmin",   "RVV", "rvv-fp-minmax", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfmax",   "RVV", "rvv-fp-minmax", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfsgnj",  "RVV", "rvv-fp-sgnj", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfsgnjn", "RVV", "rvv-fp-sgnj", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfsgnjx", "RVV", "rvv-fp-sgnj", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vfclass", "RVV", "rvv-fp-unary", "OPFVV-VFUNARY1", ["v"], FP_SEW, "supported")
add("vmfeq",   "RVV", "rvv-fp-cmp", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vmfne",   "RVV", "rvv-fp-cmp", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vmflt",   "RVV", "rvv-fp-cmp", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vmfle",   "RVV", "rvv-fp-cmp", "OPFVV/VF", ["vv", "vf"], FP_SEW, "supported")
add("vmfgt",   "RVV", "rvv-fp-cmp", "OPFVF",    ["vf"],       FP_SEW, "supported")
add("vmfge",   "RVV", "rvv-fp-cmp", "OPFVF",    ["vf"],       FP_SEW, "supported")
add("vfmerge", "RVV", "rvv-fp-merge", "OPFVF", ["vfm"], FP_SEW, "supported")
add("vfmv.v.f","RVV", "rvv-fp-merge", "OPFVF", ["f"],   FP_SEW, "supported", "FP splat")
# FP convert
add("vfcvt",   "RVV", "rvv-fp-cvt", "OPFVV-VFUNARY0", ["xu.f.v", "x.f.v", "rtz.xu.f.v", "rtz.x.f.v", "f.xu.v", "f.x.v"], FP_SEW, "supported", "same-width int<->fp convert")
add("vfwcvt",  "RVV", "rvv-fp-cvt", "OPFVV-VFUNARY0", ["xu.f.v", "x.f.v", "rtz.xu.f.v", "rtz.x.f.v", "f.xu.v", "f.x.v", "f.f.v"], [16, 32], "supported", "widening convert")
add("vfncvt",  "RVV", "rvv-fp-cvt", "OPFVV-VFUNARY0", ["xu.f.w", "x.f.w", "rtz.xu.f.w", "rtz.x.f.w", "f.xu.w", "f.x.w", "f.f.w", "rod.f.f.w"], [32, 64], "supported", "narrowing convert (incl round-to-odd)")
# widening FP
add("vfwadd",  "RVV", "rvv-fp-widen", "OPFVV/VF", ["vv", "vf", "wv", "wf"], [16, 32], "supported")
add("vfwsub",  "RVV", "rvv-fp-widen", "OPFVV/VF", ["vv", "vf", "wv", "wf"], [16, 32], "supported")
add("vfwmul",  "RVV", "rvv-fp-widen", "OPFVV/VF", ["vv", "vf"], [16, 32], "supported")
add("vfwmacc", "RVV", "rvv-fp-widen", "OPFVV/VF", ["vv", "vf"], [16, 32], "supported")
add("vfwnmacc","RVV", "rvv-fp-widen", "OPFVV/VF", ["vv", "vf"], [16, 32], "supported")
add("vfwmsac", "RVV", "rvv-fp-widen", "OPFVV/VF", ["vv", "vf"], [16, 32], "supported")
add("vfwnmsac","RVV", "rvv-fp-widen", "OPFVV/VF", ["vv", "vf"], [16, 32], "supported")
add("vfmv.f.s","RVV", "rvv-fp-scalar", "OPFVV-VWFUNARY0", ["s"], FP_SEW, "supported", "extract element0 -> f reg")
add("vfmv.s.f","RVV", "rvv-fp-scalar", "OPFVF-VRFUNARY0", ["f"], FP_SEW, "supported", "f reg -> element0")
add("vfslide1up",   "RVV", "rvv-perm", "OPFVF", ["vf"], FP_SEW, "supported")
add("vfslide1down", "RVV", "rvv-perm", "OPFVF", ["vf"], FP_SEW, "supported")

# --- reductions ------------------------------------------------------------
add("vredsum",  "RVV", "rvv-red-int", "OPMVV", ["vs"], INT_SEW, "supported")
add("vredand",  "RVV", "rvv-red-int", "OPMVV", ["vs"], INT_SEW, "supported")
add("vredor",   "RVV", "rvv-red-int", "OPMVV", ["vs"], INT_SEW, "supported")
add("vredxor",  "RVV", "rvv-red-int", "OPMVV", ["vs"], INT_SEW, "supported")
add("vredminu", "RVV", "rvv-red-int", "OPMVV", ["vs"], INT_SEW, "supported")
add("vredmin",  "RVV", "rvv-red-int", "OPMVV", ["vs"], INT_SEW, "supported")
add("vredmaxu", "RVV", "rvv-red-int", "OPMVV", ["vs"], INT_SEW, "supported")
add("vredmax",  "RVV", "rvv-red-int", "OPMVV", ["vs"], INT_SEW, "supported")
add("vwredsumu","RVV", "rvv-red-int", "OPIVV", ["vs"], WIDEN_SEW, "supported", "widening sum reduction unsigned")
add("vwredsum", "RVV", "rvv-red-int", "OPIVV", ["vs"], WIDEN_SEW, "supported")
add("vfredosum","RVV", "rvv-red-fp", "OPFVV", ["vs"], FP_SEW, "supported", "ordered FP sum (sequential)")
add("vfredusum","RVV", "rvv-red-fp", "OPFVV", ["vs"], FP_SEW, "supported", "unordered FP sum: order impl-defined, pin inputs for diff")
add("vfredmin", "RVV", "rvv-red-fp", "OPFVV", ["vs"], FP_SEW, "supported")
add("vfredmax", "RVV", "rvv-red-fp", "OPFVV", ["vs"], FP_SEW, "supported")
add("vfwredosum","RVV", "rvv-red-fp", "OPFVV", ["vs"], [16, 32], "supported", "widening ordered FP sum")
add("vfwredusum","RVV", "rvv-red-fp", "OPFVV", ["vs"], [16, 32], "supported", "widening unordered: pin inputs for diff")

# --- mask instructions -----------------------------------------------------
add("vmand",  "RVV", "rvv-mask-logical", "OPMVV-MM", ["mm"], NO_SEW, "supported")
add("vmnand", "RVV", "rvv-mask-logical", "OPMVV-MM", ["mm"], NO_SEW, "supported")
add("vmandn", "RVV", "rvv-mask-logical", "OPMVV-MM", ["mm"], NO_SEW, "supported", "and-not (a & ~b)")
add("vmxor",  "RVV", "rvv-mask-logical", "OPMVV-MM", ["mm"], NO_SEW, "supported")
add("vmor",   "RVV", "rvv-mask-logical", "OPMVV-MM", ["mm"], NO_SEW, "supported")
add("vmnor",  "RVV", "rvv-mask-logical", "OPMVV-MM", ["mm"], NO_SEW, "supported")
add("vmorn",  "RVV", "rvv-mask-logical", "OPMVV-MM", ["mm"], NO_SEW, "supported", "or-not (a | ~b)")
add("vmxnor", "RVV", "rvv-mask-logical", "OPMVV-MM", ["mm"], NO_SEW, "supported")
add("vcpop.m",  "RVV", "rvv-mask-pop", "OPMVV-VWXUNARY0", ["m"], NO_SEW, "supported", "population count of mask")
add("vfirst.m", "RVV", "rvv-mask-pop", "OPMVV-VWXUNARY0", ["m"], NO_SEW, "supported", "index of first set bit (-1 if none)")
add("vmsbf.m",  "RVV", "rvv-mask-set", "OPMVV-VMUNARY0", ["m"], NO_SEW, "supported", "set-before-first")
add("vmsif.m",  "RVV", "rvv-mask-set", "OPMVV-VMUNARY0", ["m"], NO_SEW, "supported", "set-including-first")
add("vmsof.m",  "RVV", "rvv-mask-set", "OPMVV-VMUNARY0", ["m"], NO_SEW, "supported", "set-only-first")
add("viota.m",  "RVV", "rvv-mask-iota", "OPMVV-VMUNARY0", ["m"], INT_SEW, "supported", "prefix sum of mask")
add("vid.v",    "RVV", "rvv-mask-iota", "OPMVV-VMUNARY0", ["v"], INT_SEW, "supported", "element index")
add("vmv.x.s",  "RVV", "rvv-mask-xmv", "OPMVV-VWXUNARY0", ["s"], INT_SEW, "supported", "element0 -> x reg")
add("vmv.s.x",  "RVV", "rvv-mask-xmv", "OPMVX-VRXUNARY0", ["x"], INT_SEW, "supported", "x reg -> element0")

# --- permutation -----------------------------------------------------------
add("vslideup",     "RVV", "rvv-perm", "OPIVX/VI", ["vx", "vi"], INT_SEW, "supported")
add("vslidedown",   "RVV", "rvv-perm", "OPIVX/VI", ["vx", "vi"], INT_SEW, "supported")
add("vslide1up",    "RVV", "rvv-perm", "OPMVX",    ["vx"],       INT_SEW, "supported")
add("vslide1down",  "RVV", "rvv-perm", "OPMVX",    ["vx"],       INT_SEW, "supported")
add("vrgather",     "RVV", "rvv-perm", "OPIVV/VX/VI", ["vv", "vx", "vi"], INT_SEW, "blocked_illegal", "not in op enum -> dispatcher illegal")
add("vrgatherei16", "RVV", "rvv-perm", "OPIVV",       ["vv"],             INT_SEW, "blocked_illegal", "not in op enum -> dispatcher illegal")
add("vcompress",    "RVV", "rvv-perm", "OPMVV",       ["vm"],             INT_SEW, "blocked_illegal", "not in op enum -> dispatcher illegal")
add("vmv1r.v", "RVV", "rvv-perm", "OPIVI-whole", ["v"], NO_SEW, "supported", "whole-register move (decoded as VMERGE)")
add("vmv2r.v", "RVV", "rvv-perm", "OPIVI-whole", ["v"], NO_SEW, "supported")
add("vmv4r.v", "RVV", "rvv-perm", "OPIVI-whole", ["v"], NO_SEW, "supported")
add("vmv8r.v", "RVV", "rvv-perm", "OPIVI-whole", ["v"], NO_SEW, "supported")

# ===========================================================================
# RV64 scalar (present extensions: I, M, A, F, D, C, Zicsr, Zifencei)
# ===========================================================================

# --- RV64I integer register-register + immediate ---------------------------
for m in ["add", "sub", "sll", "slt", "sltu", "xor", "srl", "sra", "or", "and"]:
    add(m, "RV64", "rv64i-reg", "R", ["r"], NO_SEW, "supported")
for m in ["addi", "slti", "sltiu", "xori", "ori", "andi", "slli", "srli", "srai"]:
    add(m, "RV64", "rv64i-imm", "I", ["i"], NO_SEW, "supported")
add("lui",   "RV64", "rv64i-imm", "U", ["u"], NO_SEW, "supported")
add("auipc", "RV64", "rv64i-imm", "U", ["u"], NO_SEW, "supported")
# RV64 word ops
for m in ["addw", "subw", "sllw", "srlw", "sraw"]:
    add(m, "RV64", "rv64i-word", "R", ["r"], NO_SEW, "supported")
for m in ["addiw", "slliw", "srliw", "sraiw"]:
    add(m, "RV64", "rv64i-word", "I", ["i"], NO_SEW, "supported")
# loads / stores
for m in ["lb", "lh", "lw", "ld", "lbu", "lhu", "lwu"]:
    add(m, "RV64", "rv64i-load", "I", ["i"], NO_SEW, "supported")
for m in ["sb", "sh", "sw", "sd"]:
    add(m, "RV64", "rv64i-store", "S", ["s"], NO_SEW, "supported")
# branches / jumps
for m in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]:
    add(m, "RV64", "rv64i-branch", "B", ["b"], NO_SEW, "supported")
add("jal",  "RV64", "rv64i-jump", "J", ["j"], NO_SEW, "supported")
add("jalr", "RV64", "rv64i-jump", "I", ["i"], NO_SEW, "supported")
add("fence",   "RV64", "rv64i-sys", "I", ["x"], NO_SEW, "supported", "Zifencei base fence")
add("fence.i", "RV64", "rv64i-sys", "I", ["x"], NO_SEW, "supported", "Zifencei")
add("ecall",   "RV64", "rv64i-sys", "I", ["x"], NO_SEW, "supported", "traps; tested via deliberate trap path")
add("ebreak",  "RV64", "rv64i-sys", "I", ["x"], NO_SEW, "supported", "traps; tested via deliberate trap path")

# --- RV64M -----------------------------------------------------------------
for m in ["mul", "mulh", "mulhsu", "mulhu", "div", "divu", "rem", "remu"]:
    add(m, "RV64", "rv64m", "R", ["r"], NO_SEW, "supported")
for m in ["mulw", "divw", "divuw", "remw", "remuw"]:
    add(m, "RV64", "rv64m", "R", ["r"], NO_SEW, "supported")

# --- RV64A (atomics) -------------------------------------------------------
add("lr.w", "RV64", "rv64a", "R", ["r"], NO_SEW, "supported")
add("sc.w", "RV64", "rv64a", "R", ["r"], NO_SEW, "supported")
add("lr.d", "RV64", "rv64a", "R", ["r"], NO_SEW, "supported")
add("sc.d", "RV64", "rv64a", "R", ["r"], NO_SEW, "supported")
for m in ["amoswap", "amoadd", "amoxor", "amoand", "amoor", "amomin", "amomax", "amominu", "amomaxu"]:
    add(f"{m}.w", "RV64", "rv64a", "R", ["r"], NO_SEW, "supported")
    add(f"{m}.d", "RV64", "rv64a", "R", ["r"], NO_SEW, "supported")

# --- RV64F (single-precision) ----------------------------------------------
add("flw", "RV64", "rv64f-mem", "I", ["i"], NO_SEW, "supported")
add("fsw", "RV64", "rv64f-mem", "S", ["s"], NO_SEW, "supported")
for m in ["fadd.s", "fsub.s", "fmul.s", "fdiv.s"]:
    add(m, "RV64", "rv64f-arith", "R", ["r"], NO_SEW, "supported")
add("fsqrt.s", "RV64", "rv64f-arith", "R", ["r"], NO_SEW, "supported")
for m in ["fmadd.s", "fmsub.s", "fnmadd.s", "fnmsub.s"]:
    add(m, "RV64", "rv64f-fma", "R4", ["r4"], NO_SEW, "supported")
for m in ["fsgnj.s", "fsgnjn.s", "fsgnjx.s", "fmin.s", "fmax.s"]:
    add(m, "RV64", "rv64f-misc", "R", ["r"], NO_SEW, "supported")
for m in ["fcvt.w.s", "fcvt.wu.s", "fcvt.s.w", "fcvt.s.wu", "fcvt.l.s", "fcvt.lu.s", "fcvt.s.l", "fcvt.s.lu"]:
    add(m, "RV64", "rv64f-cvt", "R", ["r"], NO_SEW, "supported")
for m in ["fmv.x.w", "fmv.w.x", "feq.s", "flt.s", "fle.s", "fclass.s"]:
    add(m, "RV64", "rv64f-misc", "R", ["r"], NO_SEW, "supported")

# --- RV64D (double-precision) ----------------------------------------------
add("fld", "RV64", "rv64d-mem", "I", ["i"], NO_SEW, "supported")
add("fsd", "RV64", "rv64d-mem", "S", ["s"], NO_SEW, "supported")
for m in ["fadd.d", "fsub.d", "fmul.d", "fdiv.d"]:
    add(m, "RV64", "rv64d-arith", "R", ["r"], NO_SEW, "supported")
add("fsqrt.d", "RV64", "rv64d-arith", "R", ["r"], NO_SEW, "supported")
for m in ["fmadd.d", "fmsub.d", "fnmadd.d", "fnmsub.d"]:
    add(m, "RV64", "rv64d-fma", "R4", ["r4"], NO_SEW, "supported")
for m in ["fsgnj.d", "fsgnjn.d", "fsgnjx.d", "fmin.d", "fmax.d"]:
    add(m, "RV64", "rv64d-misc", "R", ["r"], NO_SEW, "supported")
for m in ["fcvt.s.d", "fcvt.d.s", "fcvt.w.d", "fcvt.wu.d", "fcvt.d.w", "fcvt.d.wu",
          "fcvt.l.d", "fcvt.lu.d", "fcvt.d.l", "fcvt.d.lu"]:
    add(m, "RV64", "rv64d-cvt", "R", ["r"], NO_SEW, "supported")
for m in ["fmv.x.d", "fmv.d.x", "feq.d", "flt.d", "fle.d", "fclass.d"]:
    add(m, "RV64", "rv64d-misc", "R", ["r"], NO_SEW, "supported")

# --- Zicsr -----------------------------------------------------------------
for m in ["csrrw", "csrrs", "csrrc", "csrrwi", "csrrsi", "csrrci"]:
    add(m, "RV64", "zicsr", "I", ["i"], NO_SEW, "supported", "read/write CSR (e.g. vl, vtype, fcsr, cycle)")

# --- RV64C (compressed) ----------------------------------------------------
# Compressed forms are emitted implicitly by the assembler whenever -march has
# 'c'. They are exercised by EVERY compiled kernel rather than as standalone
# directed tests; tracked as one coverage row.
add("c.*", "RV64", "rv64c", "C", ["c"], NO_SEW, "supported", "compressed 16-bit forms; exercised implicitly by all compiled code")

# ===========================================================================
# Absent scalar extensions (NOT in this CVA6 config) - out of scope
# ===========================================================================
for m, ext_note in [
    ("Zba (sh1add/sh2add/sh3add/add.uw/...)", "address-gen bitmanip"),
    ("Zbb (andn/orn/xnor/clz/ctz/cpop/min/max/rev8/...)", "basic bitmanip"),
    ("Zbc (clmul/clmulh/clmulr)", "carry-less multiply"),
    ("Zbs (bclr/bext/binv/bset)", "single-bit bitmanip"),
    ("Zicond (czero.eqz/czero.nez)", "conditional zero"),
    ("Zcb/Zcmp", "extra compressed"),
    ("Zfh (scalar flh/fsh/fcvt.h.*)", "scalar half precision"),
]:
    add(m, "RV64", "absent-ext", "-", [], NO_SEW, "absent_ext", f"{ext_note}: CVA6ConfigBExtEn=0 / not instantiated; would trap illegal")


# ---------------------------------------------------------------------------
# emit
# ---------------------------------------------------------------------------
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    # json
    with open(os.path.join(here, "inventory.json"), "w") as f:
        json.dump(_entries, f, indent=2)
    # csv
    cols = ["mnemonic", "ext", "group", "format", "forms", "sew", "expected", "note"]
    with open(os.path.join(here, "inventory.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for e in _entries:
            w.writerow([
                e["mnemonic"], e["ext"], e["group"], e["format"],
                "|".join(e["forms"]), "|".join(str(s) for s in e["sew"]),
                e["expected"], e["note"],
            ])
    # markdown (skimmable)
    with open(os.path.join(here, "inventory.md"), "w") as f:
        f.write("# Instruction inventory (RVV 1.0 + RV64 scalar)\n\n")
        # summary counts
        n_total = len(_entries)
        n_rvv = sum(1 for e in _entries if e["ext"] == "RVV")
        n_rv64 = sum(1 for e in _entries if e["ext"] == "RV64")
        by_exp = {}
        for e in _entries:
            by_exp[e["expected"]] = by_exp.get(e["expected"], 0) + 1
        f.write(f"- Total base mnemonics: **{n_total}** (RVV {n_rvv}, RV64 {n_rv64})\n")
        for k in sorted(by_exp):
            f.write(f"- expected `{k}`: {by_exp[k]}\n")
        f.write("\n| Mnemonic | Ext | Group | Format | Forms | SEW | Expected | Note |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for e in _entries:
            f.write("| `{m}` | {x} | {g} | {fmt} | {fo} | {s} | {e} | {n} |\n".format(
                m=e["mnemonic"], x=e["ext"], g=e["group"], fmt=e["format"],
                fo=" ".join(e["forms"]), s=",".join(str(s) for s in e["sew"]),
                e=e["expected"], n=e["note"]))
    print(f"wrote inventory.json/.csv/.md ({n_total} entries) to {here}")
    print(f"  RVV={n_rvv} RV64={n_rv64}")
    for k in sorted(by_exp):
        print(f"  expected[{k}]={by_exp[k]}")


if __name__ == "__main__":
    main()
