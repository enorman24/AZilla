#!/usr/bin/env python3
"""
gen_kernels.py - generate directed RVV verification kernels from the inventory.

One committed .c kernel per base mnemonic, exercising a representative-broad
variant matrix (SEW x LMUL x form x masked x edge) as a sequence of #V blocks
that the differential harness (verify_one.py) verdicts per-variant.

Key constraints baked in:
  * AVL clamped to VLMAX_spike(SEW,LMUL) (Spike oracle caps vlen at 4096 while
    AraXL VLEN=16384) so both sims process identical vl/data.
  * result extraction is always unit-stride vse to a 128B-aligned .l2 buffer
    (AraXL deadlocks on non-64B-aligned vector stores).
  * masked variants use mask-undisturbed (mu) with a preloaded destination;
    tail not dumped (agnostic fill is implementation-defined). vl=0 uses tu.

This file emits the RVV-INTEGER class (call with --groups). FP/mem/scalar
classes are added in later stages.
"""
import argparse
import json
import os
import struct

SPIKE_VLEN = 4096
LMUL_VAL = {"m1": 1.0, "m2": 2.0, "m4": 4.0, "m8": 8.0,
            "mf2": 0.5, "mf4": 0.25, "mf8": 0.125}


def vlmax(sew, lmul):
    return int(SPIKE_VLEN * LMUL_VAL[lmul] / sew)


def lmul_ok(sew, lmul):
    # fractional LMUL requires LMUL >= SEW/ELEN (ELEN=64); need >=2 elements
    return LMUL_VAL[lmul] >= sew / 64.0 and vlmax(sew, lmul) >= 2


def avl_for(sew, lmul, target=37):
    return max(1, min(target, vlmax(sew, lmul)))


def dump_w(sew):
    return {8: "report_e8", 16: "report_e16", 32: "report_e32", 64: "report_e64"}[sew]


# ---------------------------------------------------------------------------
# per-kind asm emitters: each returns a C statement block (string) for ONE
# variant. v8/v16 = sources, v24 = dest, v0 = mask. A,B,R,D0,M are .l2 pools.
# asm_block joins a list of instruction strings into an asm volatile statement.
# ---------------------------------------------------------------------------
def asm_block(instrs, operands, clobbers='"t0","t1","memory"'):
    # instrs contain literal %[A]-style operand refs; do NOT %-format them.
    body = "\n".join('    "' + i + '\\n"' for i in instrs)
    return ("    asm volatile(\n" + body +
            "\n    :: " + operands + " : " + clobbers + ");\n")


def emit_vec(mn, form, sew, lmul, masked, vl0, reads_vd):
    """standard vec op: result EEW = vtype SEW. forms vv/vx/vi."""
    s = sew
    avl = avl_for(s, lmul)
    operands = f'[A]"r"(A),[B]"r"(B),[R]"r"(R),[D]"r"(D0),[M]"r"(M),[vl]"r"({avl}UL)'
    src = [f"vle{s}.v v8,(%[A])"]
    if form == "vv":
        src.append(f"vle{s}.v v16,(%[B])")
    if form == "vx":
        src = ["li t1,19"] + src
    # muladd .vx uses operand order (vd, rs1=scalar, vs2=vector); other .vx use
    # (vd, vs2, rs1). .vv text is identical either way (vd, op2, op3 = v8, v16).
    vx_op = f"{mn}.vx v24,t1,v8" if reads_vd else f"{mn}.vx v24,v8,t1"
    opcore = {"vv": f"{mn}.vv v24,v8,v16", "vx": vx_op,
              "vi": f"{mn}.vi v24,v8,5"}[form]

    if vl0:
        lbl = f"{mn}.{form} e{s} {lmul} vl=0(dest preserved)"
        instrs = ([f"vsetivli t0,8,e{s},{lmul},ta,ma", f"vle{s}.v v24,(%[D])",
                   f"vsetvli t0,zero,e{s},{lmul},tu,ma"] + src + [opcore,
                  f"vsetivli t0,8,e{s},{lmul},ta,ma", f"vse{s}.v v24,(%[R])"])
        return asm_block(instrs, '[A]"r"(A),[B]"r"(B),[R]"r"(R),[D]"r"(D0)') + \
            f'    {dump_w(s)}("{lbl}", R, 8);\n'

    if masked:
        lbl = f"{mn}.{form} e{s} {lmul} masked(mu) avl={avl}"
        instrs = ([f"vsetvli t0,%[vl],e{s},{lmul},ta,mu",
                   "vlm.v v0,(%[M])", f"vle{s}.v v24,(%[D])"] + src +
                  [opcore + ",v0.t", f"vse{s}.v v24,(%[R])"])
        return asm_block(instrs, operands) + f'    {dump_w(s)}("{lbl}", R, {avl});\n'

    lbl = f"{mn}.{form} e{s} {lmul} avl={avl}"
    pre = [f"vle{s}.v v24,(%[D])"] if reads_vd else []
    instrs = ([f"vsetvli t0,%[vl],e{s},{lmul},ta,ma"] + pre + src +
              [opcore, f"vse{s}.v v24,(%[R])"])
    return asm_block(instrs, operands) + f'    {dump_w(s)}("{lbl}", R, {avl});\n'


def emit_cmp(mn, form, sew, lmul):
    """compare -> mask. dump ceil(vl/8) bytes; vl forced multiple of 8."""
    s = sew
    avl = (avl_for(s, lmul) // 8) * 8
    if avl < 8:
        avl = min(8, vlmax(s, lmul))
    nbytes = (avl + 7) // 8
    op = {"vv": f"{mn}.vv v24,v8,v16", "vx": f"{mn}.vx v24,v8,t1",
          "vi": f"{mn}.vi v24,v8,5"}[form]
    load_b = f'    "vle{s}.v v16,(%[B])\\n"\n' if form == "vv" else ""
    scal = '    "li t1,19\\n"\n' if form == "vx" else ""
    lbl = f"{mn}.{form} e{s} {lmul} vl={avl}"
    body = (
        f'    asm volatile(\n'
        f'    "vsetvli t0,%[vl],e{s},{lmul},ta,ma\\n"\n'
        f'    "vle{s}.v v8,(%[A])\\n"\n{load_b}{scal}'
        f'    "{op}\\n vsm.v v24,(%[R])\\n"\n'
        f'    :: [A]"r"(A),[B]"r"(B),[R]"r"(R),[vl]"r"({avl}UL) : "t0","t1","memory");\n'
        f'    report_bytes("{lbl}", R, {nbytes});\n')
    return body


def emit_widen(mn, form, sew, lmul):
    """widening: sources EEW=SEW (EMUL=LMUL), result EEW=2*SEW (EMUL=2*LMUL).
    forms vv/vx (both src narrow) and wv/wx (vs2 already wide)."""
    s = sew
    avl = avl_for(s, lmul)
    w = 2 * s
    wl = {"m1": "m2", "m2": "m4", "m4": "m8", "mf2": "m1", "mf4": "mf2", "mf8": "mf4"}[lmul]
    lbl = f"{mn}.{form} e{s}->e{w} {lmul} avl={avl}"
    if form in ("vv", "vx"):
        reads_vd = mn.startswith("vwmacc")   # widening multiply-accumulate
        scal = '    "li t1,7\\n"\n' if form == "vx" else ""
        # muladd .vx uses (vd, rs1, vs2) order; other widening .vx use (vd, vs2, rs1)
        if form == "vv":
            opb = f"{mn}.vv v24,v8,v16"
        else:
            opb = f"{mn}.vx v24,t1,v8" if reads_vd else f"{mn}.vx v24,v8,t1"
        load_b = f'    "vle{s}.v v16,(%[B])\\n"\n' if form == "vv" else ""
        # accumulator vd is wide; preload it deterministically for muladd
        preload = f'    "vsetvli t0,%[vl],e{w},{wl},ta,ma\\n vle{w}.v v24,(%[D])\\n"\n' if reads_vd else ""
        body = (
            f'    asm volatile(\n'
            f'{preload}'
            f'    "vsetvli t0,%[vl],e{s},{lmul},ta,ma\\n"\n'
            f'    "vle{s}.v v8,(%[A])\\n"\n{load_b}{scal}'
            f'    "{opb}\\n"\n'
            f'    "vsetvli t0,%[vl],e{w},{wl},ta,ma\\n vse{w}.v v24,(%[R])\\n"\n'
            f'    :: [A]"r"(A),[B]"r"(B),[R]"r"(R),[D]"r"(D0),[vl]"r"({avl}UL) : "t0","t1","memory");\n'
            f'    {dump_w(w)}("{lbl}", R, {avl});\n')
    else:  # wv / wx : vs2 is wide (EEW=2*SEW), vs1/rs1 narrow
        scal = '    "li t1,7\\n"\n' if form == "wx" else ""
        opb = f"{mn}.wv v24,v8,v16" if form == "wv" else f"{mn}.wx v24,v8,t1"
        load_b = f'    "vsetvli t0,%[vl],e{s},{lmul},ta,ma\\n vle{s}.v v16,(%[B])\\n"\n' if form == "wv" else ""
        body = (
            f'    asm volatile(\n'
            f'    "vsetvli t0,%[vl],e{w},{wl},ta,ma\\n vle{w}.v v8,(%[A])\\n"\n'
            f'{load_b}{scal}'
            f'    "vsetvli t0,%[vl],e{s},{lmul},ta,ma\\n"\n'
            f'    "{opb}\\n"\n'
            f'    "vsetvli t0,%[vl],e{w},{wl},ta,ma\\n vse{w}.v v24,(%[R])\\n"\n'
            f'    :: [A]"r"(A),[B]"r"(B),[R]"r"(R),[vl]"r"({avl}UL) : "t0","t1","memory");\n'
            f'    {dump_w(w)}("{lbl}", R, {avl});\n')
    return body


def emit_narrow(mn, form, sew, lmul):
    """narrowing: vs2 wide (EEW=2*SEW), result narrow (EEW=SEW). forms wv/wx/wi."""
    s = sew  # destination SEW (inventory sew = source/wide EEW for narrow rows)
    # here sew passed in is the SOURCE (wide) width per inventory convention;
    # destination is sew/2.
    dst = s // 2
    avl = avl_for(s, lmul)  # clamp by wide side
    wl = {"m1": "m2", "m2": "m4", "m4": "m8", "mf2": "m1", "mf4": "mf2"}.get(lmul, "m8")
    lbl = f"{mn}.{form} e{s}->e{dst} {lmul} avl={avl}"
    if form == "wv":
        opb = f"{mn}.wv v24,v8,v16"
        load_b = f'    "vsetvli t0,%[vl],e{dst},{lmul},ta,ma\\n vle{dst}.v v16,(%[B])\\n"\n'
        scal = ""
    elif form == "wx":
        opb = f"{mn}.wx v24,v8,t1"; load_b = ""; scal = '    "li t1,3\\n"\n'
    else:
        opb = f"{mn}.wi v24,v8,3"; load_b = ""; scal = ""
    body = (
        f'    asm volatile(\n'
        f'    "vsetvli t0,%[vl],e{s},{wl},ta,ma\\n vle{s}.v v8,(%[A])\\n"\n'
        f'{load_b}{scal}'
        f'    "vsetvli t0,%[vl],e{dst},{lmul},ta,ma\\n"\n'
        f'    "{opb}\\n vse{dst}.v v24,(%[R])\\n"\n'
        f'    :: [A]"r"(A),[B]"r"(B),[R]"r"(R),[vl]"r"({avl}UL) : "t0","t1","memory");\n'
        f'    {dump_w(dst)}("{lbl}", R, {avl});\n')
    return body


def emit_ext(mn, form, lmul):
    """vzext/vsext .vfN : dest SEW = N * source SEW. forms vf2/vf4/vf8."""
    n = {"vf2": 2, "vf4": 4, "vf8": 8}[form]
    dst = {2: [16, 32, 64], 4: [32, 64], 8: [64]}[n][0]  # smallest valid dest
    src = dst // n
    avl = avl_for(dst, lmul)
    sl = {1.0: {16: "mf2", 32: "mf4", 64: "mf8"}}  # not used; compute src lmul
    lbl = f"{mn}.{form} e{src}->e{dst} {lmul} avl={avl}"
    body = (
        f'    asm volatile(\n'
        f'    "vsetvli t0,%[vl],e{dst},{lmul},ta,ma\\n"\n'
        f'    "vle{src}.v v8,(%[A])\\n"\n'
        f'    "{mn}.{form} v24,v8\\n vse{dst}.v v24,(%[R])\\n"\n'
        f'    :: [A]"r"(A),[R]"r"(R),[vl]"r"({avl}UL) : "t0","memory");\n'
        f'    {dump_w(dst)}("{lbl}", R, {avl});\n')
    return body


def emit_merge(mn, form, sew, lmul):
    """vmerge.vvm/vxm/vim (mask-select, v0 explicit) and vmv.v.v/.v.x/.v.i."""
    s = sew
    avl = avl_for(s, lmul)
    operands = f'[A]"r"(A),[B]"r"(B),[R]"r"(R),[M]"r"(M),[vl]"r"({avl}UL)'
    if mn == "vmerge":
        src = [f"vle{s}.v v8,(%[A])"]
        if form == "vvm":
            src.append(f"vle{s}.v v16,(%[B])"); op = "vmerge.vvm v24,v8,v16,v0"
        elif form == "vxm":
            src = ["li t1,21"] + src; op = "vmerge.vxm v24,v8,t1,v0"
        else:
            op = "vmerge.vim v24,v8,5,v0"
        instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", "vlm.v v0,(%[M])"] + src + \
                 [op, f"vse{s}.v v24,(%[R])"]
        lbl = f"vmerge.{form} e{s} {lmul} avl={avl}"
    else:  # vmv.v
        if form == "v":
            src = [f"vle{s}.v v8,(%[A])"]; op = "vmv.v.v v24,v8"
        elif form == "x":
            src = ["li t1,21"]; op = "vmv.v.x v24,t1"
        else:
            src = []; op = "vmv.v.i v24,5"
        instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma"] + src + [op, f"vse{s}.v v24,(%[R])"]
        lbl = f"vmv.v.{form} e{s} {lmul} avl={avl}"
    return asm_block(instrs, operands) + f'    {dump_w(s)}("{lbl}", R, {avl});\n'


def emit_carry(mn, form, sew, lmul):
    """vadc/vsbc (vec result, carry-in v0) and vmadc/vmsbc (mask result, with or
    without carry-in)."""
    s = sew
    mask_result = mn in ("vmadc", "vmsbc")
    carry_in = form.endswith("m")
    base = form[:-1] if carry_in else form
    if mask_result:
        avl = (avl_for(s, lmul) // 8) * 8 or min(8, vlmax(s, lmul))
    else:
        avl = avl_for(s, lmul)
    operands = f'[A]"r"(A),[B]"r"(B),[R]"r"(R),[M]"r"(M),[vl]"r"({avl}UL)'
    src = [f"vle{s}.v v8,(%[A])"]
    if base == "vv":
        src.append(f"vle{s}.v v16,(%[B])"); ops = "v24,v8,v16"
    elif base == "vx":
        src = ["li t1,21"] + src; ops = "v24,v8,t1"
    else:
        ops = "v24,v8,5"
    op = f"{mn}.{form} {ops}" + (",v0" if carry_in else "")
    pre = ["vlm.v v0,(%[M])"] if carry_in else []
    store = "vsm.v v24,(%[R])" if mask_result else f"vse{s}.v v24,(%[R])"
    instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma"] + pre + src + [op, store]
    lbl = f"{mn}.{form} e{s} {lmul} avl={avl}"
    if mask_result:
        return asm_block(instrs, operands) + f'    report_bytes("{lbl}", R, {(avl + 7) // 8});\n'
    return asm_block(instrs, operands) + f'    {dump_w(s)}("{lbl}", R, {avl});\n'


# ---------------------------------------------------------------------------
# Floating-point: curated input values (bit-exact differential incl. specials).
# Computed as raw bit patterns so the host -ffast-math can never fold them.
# all values are half-precision representable (|v| <= 65504) so the same list
# packs into f16/f32/f64 pools without overflow.
_FP_BASE = [0.0, -0.0, 1.0, -1.0, 0.5, -0.5, 2.5, -3.25, 3.5, 0.125, -0.1,
            10.0, -100.0, 1234.5, -0.001953125, 7.0, -2.0, 255.0, 0.33333333, -15.5,
            65504.0, 6.103515625e-05, 3.14159265, -2.71828, 0.0078125, 8192.0]
_FPN = 96


def _bits(vals, pk, uk, off=0):
    return [struct.unpack(uk, struct.pack(pk, vals[(i + off) % len(vals)]))[0]
            for i in range(_FPN)]


def _cinit(name, ctype, fmt, values):
    body = ", ".join(fmt % v for v in values)
    return f"static {ctype} {name}[{_FPN}] L2BUF = {{ {body} }};\n"


def fp_pools():
    out = ""
    for w, ctype, pk, uk, fmt in [(16, "uint16_t", "<e", "<H", "0x%04x"),
                                  (32, "uint32_t", "<f", "<I", "0x%08x"),
                                  (64, "uint64_t", "<d", "<Q", "0x%016xULL")]:
        out += _cinit(f"FA{w}", ctype, fmt, _bits(_FP_BASE, pk, uk, 0))
        out += _cinit(f"FB{w}", ctype, fmt, _bits(_FP_BASE, pk, uk, 5))
        out += _cinit(f"FC{w}", ctype, fmt, _bits(_FP_BASE, pk, uk, 9))
    return out


FL = {16: "flh", 32: "flw", 64: "fld"}


def emit_fp(mn, form, sew, lmul, reads_vd):
    s = sew; avl = avl_for(s, lmul)
    A, B, C = f"FA{s}", f"FB{s}", f"FC{s}"
    operands = f'[A]"r"({A}),[B]"r"({B}),[C]"r"({C}),[R]"r"(R),[vl]"r"({avl}UL)'
    pre = [f"vle{s}.v v24,(%[C])"] if reads_vd else []
    if form == "vv":
        src = [f"vle{s}.v v8,(%[A])", f"vle{s}.v v16,(%[B])"]
        op = f"{mn}.vv v24,v8,v16"
    else:  # vf
        src = [f"{FL[s]} ft0,0(%[B])", f"vle{s}.v v8,(%[A])"]
        op = (f"{mn}.vf v24,ft0,v8" if reads_vd else f"{mn}.vf v24,v8,ft0")
    instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma"] + pre + src + [op, f"vse{s}.v v24,(%[R])"]
    lbl = f"{mn}.{form} e{s} {lmul} avl={avl}"
    return asm_block(instrs, operands, '"t0","ft0","memory"') + f'    {dump_w(s)}("{lbl}", R, {avl});\n'


def emit_fp_unary(mn, sew, lmul):
    s = sew; avl = avl_for(s, lmul)
    operands = f'[A]"r"(FA{s}),[R]"r"(R),[vl]"r"({avl}UL)'
    instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", f"vle{s}.v v8,(%[A])",
              f"{mn}.v v24,v8", f"vse{s}.v v24,(%[R])"]
    lbl = f"{mn}.v e{s} {lmul} avl={avl}"
    return asm_block(instrs, operands) + f'    {dump_w(s)}("{lbl}", R, {avl});\n'


def emit_fp_cmp(mn, form, sew, lmul):
    s = sew
    avl = (avl_for(s, lmul) // 8) * 8 or min(8, vlmax(s, lmul))
    operands = f'[A]"r"(FA{s}),[B]"r"(FB{s}),[R]"r"(R),[vl]"r"({avl}UL)'
    if form == "vv":
        src = [f"vle{s}.v v8,(%[A])", f"vle{s}.v v16,(%[B])"]; op = f"{mn}.vv v24,v8,v16"
    else:
        src = [f"{FL[s]} ft0,0(%[B])", f"vle{s}.v v8,(%[A])"]; op = f"{mn}.vf v24,v8,ft0"
    instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma"] + src + [op, "vsm.v v24,(%[R])"]
    lbl = f"{mn}.{form} e{s} {lmul} vl={avl}"
    return asm_block(instrs, operands, '"t0","ft0","memory"') + f'    report_bytes("{lbl}", R, {(avl + 7) // 8});\n'


def emit_fp_merge(mn, form, sew, lmul):
    s = sew; avl = avl_for(s, lmul)
    if mn == "vfmerge":   # vfmerge.vfm v24,v8,ft0,v0
        operands = f'[A]"r"(FA{s}),[B]"r"(FB{s}),[R]"r"(R),[M]"r"(M),[vl]"r"({avl}UL)'
        instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", "vlm.v v0,(%[M])",
                  f"{FL[s]} ft0,0(%[B])", f"vle{s}.v v8,(%[A])",
                  "vfmerge.vfm v24,v8,ft0,v0", f"vse{s}.v v24,(%[R])"]
        lbl = f"vfmerge.vfm e{s} {lmul} avl={avl}"
    else:                 # vfmv.v.f v24,ft0
        operands = f'[B]"r"(FB{s}),[R]"r"(R),[vl]"r"({avl}UL)'
        instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", f"{FL[s]} ft0,0(%[B])",
                  "vfmv.v.f v24,ft0", f"vse{s}.v v24,(%[R])"]
        lbl = f"vfmv.v.f e{s} {lmul} avl={avl}"
    return asm_block(instrs, operands, '"t0","ft0","memory"') + f'    {dump_w(s)}("{lbl}", R, {avl});\n'


def emit_fp_scalar(mn, sew, lmul):
    s = sew; avl = avl_for(s, lmul)
    if mn == "vfmv.f.s":   # element0 -> f reg -> store
        operands = f'[A]"r"(FA{s}),[R]"r"(R),[vl]"r"({avl}UL)'
        st = {16: "fsh", 32: "fsw", 64: "fsd"}[s]
        instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", f"vle{s}.v v8,(%[A])",
                  "vfmv.f.s ft0,v8", f"{st} ft0,0(%[R])"]
        lbl = f"vfmv.f.s e{s} {lmul}"
        return asm_block(instrs, operands, '"t0","ft0","memory"') + f'    {dump_w(s)}("{lbl}", R, 1);\n'
    else:                  # vfmv.s.f : f reg -> element0
        operands = f'[B]"r"(FB{s}),[R]"r"(R),[vl]"r"({avl}UL)'
        instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", f"{FL[s]} ft0,0(%[B])",
                  "vfmv.s.f v24,ft0", f"vse{s}.v v24,(%[R])"]
        lbl = f"vfmv.s.f e{s} {lmul}"
        return asm_block(instrs, operands, '"t0","ft0","memory"') + f'    {dump_w(s)}("{lbl}", R, 1);\n'


def emit_fp_widen(mn, form, sew, lmul):
    s = sew; avl = avl_for(s, lmul); w = 2 * s
    wl = {"m1": "m2", "m2": "m4", "m4": "m8", "mf2": "m1", "mf4": "mf2"}.get(lmul, "m8")
    reads_vd = mn in ("vfwmacc", "vfwnmacc", "vfwmsac", "vfwnmsac")  # widening FP FMA
    lbl = f"{mn}.{form} e{s}->e{w} {lmul} avl={avl}"
    nv = f"vsetvli t0,%[vl],e{s},{lmul},ta,ma"   # narrow vtype (op executes here)
    wv = f"vsetvli t0,%[vl],e{w},{wl},ta,ma"     # wide vtype (vd load/store)
    pre = [wv, f"vle{w}.v v24,(%[C])"] if reads_vd else []
    if form in ("vv", "vf"):
        if form == "vv":
            src = [nv, f"vle{s}.v v8,(%[A])", f"vle{s}.v v16,(%[B])"]
            op = f"{mn}.vv v24,v8,v16"
        else:
            src = [nv, f"{FL[s]} ft0,0(%[B])", f"vle{s}.v v8,(%[A])"]
            # FMA .vf order is (vd, rs1, vs2); plain widen .vf is (vd, vs2, rs1)
            op = f"{mn}.vf v24,ft0,v8" if reads_vd else f"{mn}.vf v24,v8,ft0"
        instrs = pre + src + [op, wv, f"vse{w}.v v24,(%[R])"]
    else:  # wv/wf : vs2 already wide (EEW=2*SEW); op runs at the NARROW vtype
        loadw = [wv, f"vle{w}.v v8,(%[A])"]
        if form == "wv":
            src = [nv, f"vle{s}.v v16,(%[B])"]; op = f"{mn}.wv v24,v8,v16"
        else:   # wf scalar is narrow-width (SEW)
            src = [nv, f"{FL[s]} ft0,0(%[B])"]; op = f"{mn}.wf v24,v8,ft0"
        instrs = loadw + src + [op, wv, f"vse{w}.v v24,(%[R])"]
    operands = f'[A]"r"(FA{s}),[B]"r"(FB{s}),[C]"r"(FC{w}),[R]"r"(R),[vl]"r"({avl}UL)'
    return asm_block(instrs, operands, '"t0","ft0","memory"') + f'    {dump_w(w)}("{lbl}", R, {avl});\n'


def emit_fp_cvt(mn, suffix, sew, lmul):
    """vfcvt (same width), vfwcvt (->2x), vfncvt (2x->1x). suffix e.g. x.f.v.
    The convert EXECUTES at the NARROW SEW (= source for widening, dest for
    narrowing); only the load/store use their own widths."""
    s = sew; avl = avl_for(s, lmul)
    W = {"m1": "m2", "m2": "m4", "m4": "m8", "mf2": "m1", "mf4": "mf2"}
    if mn == "vfwcvt":          # narrow = source
        src_w, dst_w = s, 2 * s
        sl, dl = lmul, W.get(lmul, "m8")
        op_w, op_lmul = src_w, sl
    elif mn == "vfncvt":        # narrow = dest
        src_w, dst_w = 2 * s, s
        dl, sl = lmul, W.get(lmul, "m8")
        op_w, op_lmul = dst_w, dl
    else:                       # vfcvt: same width
        src_w = dst_w = op_w = s; sl = dl = op_lmul = lmul
    operands = f'[A]"r"(FA{src_w}),[R]"r"(R),[vl]"r"({avl}UL)'
    instrs = [f"vsetvli t0,%[vl],e{src_w},{sl},ta,ma", f"vle{src_w}.v v8,(%[A])",
              f"vsetvli t0,%[vl],e{op_w},{op_lmul},ta,ma", f"{mn}.{suffix} v24,v8",
              f"vsetvli t0,%[vl],e{dst_w},{dl},ta,ma", f"vse{dst_w}.v v24,(%[R])"]
    lbl = f"{mn}.{suffix} e{src_w}->e{dst_w} {lmul} avl={avl}"
    return asm_block(instrs, operands) + f'    {dump_w(dst_w)}("{lbl}", R, {avl});\n'


# ---------------------------------------------------------------------------
# reductions, mask ops, permutes, config
def emit_red(mn, sew, lmul, fp):
    """reduction .vs: vd[0] = vs1[0] (op) reduce(vs2[0..vl-1]). seed via element0."""
    s = sew; avl = avl_for(s, lmul)
    pool = f"FA{s}" if fp else "A"
    operands = f'[A]"r"({pool}),[R]"r"(R),[vl]"r"({avl}UL)'
    # seed: for fp use vfmv.s.f from a known value; for int use vmv.s.x
    if fp:
        seed = [f"{FL[s]} ft0,0(%[A])", "vfmv.s.f v4,ft0"]
        clob = '"t0","ft0","memory"'
    else:
        seed = ["li t1,1", "vmv.s.x v4,t1"]
        clob = '"t0","t1","memory"'
    instrs = ([f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", f"vle{s}.v v8,(%[A])"] + seed +
              [f"{mn}.vs v24,v8,v4", f"vse{s}.v v24,(%[R])"])
    lbl = f"{mn}.vs e{s} {lmul} avl={avl}"
    return asm_block(instrs, operands, clob) + f'    {dump_w(s)}("{lbl}", R, 1);\n'


def emit_red_w(mn, sew, lmul, fp):
    """widening reduction: vs2 EEW=SEW, vd[0]/vs1 EEW=2*SEW."""
    s = sew; avl = avl_for(s, lmul); w = 2 * s
    wl = {"m1": "m2", "m2": "m4", "m4": "m8", "mf2": "m1", "mf4": "mf2"}.get(lmul, "m8")
    pool = f"FA{s}" if fp else "A"
    operands = f'[A]"r"({pool}),[R]"r"(R),[vl]"r"({avl}UL)'
    # seed vs1[0] at the WIDE width (vd/vs1 are 2*SEW); then switch to the NARROW
    # vtype for the reduction itself (vs2 is SEW); then wide vtype to store vd[0].
    if fp:
        seed = [f"vsetvli t0,%[vl],e{w},{wl},ta,ma", f"{FL[w]} ft0,0(%[A])", "vfmv.s.f v4,ft0"]
        clob = '"t0","ft0","memory"'
    else:
        seed = [f"vsetvli t0,%[vl],e{w},{wl},ta,ma", "li t1,1", "vmv.s.x v4,t1"]
        clob = '"t0","t1","memory"'
    instrs = (seed +
              [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", f"vle{s}.v v8,(%[A])",
               f"{mn}.vs v24,v8,v4",
               f"vsetvli t0,%[vl],e{w},{wl},ta,ma", f"vse{w}.v v24,(%[R])"])
    lbl = f"{mn}.vs e{s}->e{w} {lmul} avl={avl}"
    return asm_block(instrs, operands, clob) + f'    {dump_w(w)}("{lbl}", R, 1);\n'


def emit_mask_logical(mn, lmul):
    """vmand/vmor/... .mm operate on mask regs. vl chosen multiple of 8."""
    avl = 32
    operands = '[A]"r"(A),[B]"r"(B),[R]"r"(R),[vl]"r"(%dUL)' % avl
    instrs = [f"vsetvli t0,%[vl],e8,{lmul},ta,ma", "vlm.v v0,(%[A])", "vlm.v v8,(%[B])",
              f"{mn}.mm v24,v0,v8", "vsm.v v24,(%[R])"]
    lbl = f"{mn}.mm {lmul} vl={avl}"
    return asm_block(instrs, operands) + f'    report_bytes("{lbl}", R, {avl // 8});\n'


def emit_mask_pop(mn, lmul):
    """vcpop.m / vfirst.m -> scalar x result."""
    avl = 64
    operands = '[A]"r"(A),[R]"r"(R),[vl]"r"(%dUL)' % avl
    instrs = [f"vsetvli t0,%[vl],e8,{lmul},ta,ma", "vlm.v v0,(%[A])",
              f"{mn} t1,v0", "sd t1,0(%[R])"]
    lbl = f"{mn} {lmul} vl={avl}"
    return asm_block(instrs, operands) + f'    report_e64("{lbl}", R, 1);\n'


def emit_mask_set(mn, lmul):
    """vmsbf/vmsif/vmsof .m -> mask result."""
    avl = 32
    operands = '[A]"r"(A),[R]"r"(R),[vl]"r"(%dUL)' % avl
    instrs = [f"vsetvli t0,%[vl],e8,{lmul},ta,ma", "vlm.v v0,(%[A])",
              f"{mn} v24,v0", "vsm.v v24,(%[R])"]
    lbl = f"{mn} {lmul} vl={avl}"
    return asm_block(instrs, operands) + f'    report_bytes("{lbl}", R, {avl // 8});\n'


def emit_iota(mn, sew, lmul):
    """viota.m (mask->vec prefix-sum) / vid.v (element index -> vec)."""
    s = sew; avl = avl_for(s, lmul)
    operands = f'[A]"r"(A),[R]"r"(R),[vl]"r"({avl}UL)'
    if mn == "viota.m":
        instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", "vlm.v v0,(%[A])",
                  "viota.m v24,v0", f"vse{s}.v v24,(%[R])"]
    else:
        instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", "vid.v v24", f"vse{s}.v v24,(%[R])"]
    lbl = f"{mn} e{s} {lmul} avl={avl}"
    return asm_block(instrs, operands) + f'    {dump_w(s)}("{lbl}", R, {avl});\n'


def emit_xmv(mn, sew, lmul):
    """vmv.x.s (element0 -> x) / vmv.s.x (x -> element0)."""
    s = sew; avl = avl_for(s, lmul)
    if mn == "vmv.x.s":
        operands = f'[A]"r"(A),[R]"r"(R),[vl]"r"({avl}UL)'
        instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", f"vle{s}.v v8,(%[A])",
                  "vmv.x.s t1,v8", "sd t1,0(%[R])"]
        lbl = f"vmv.x.s e{s} {lmul}"
        return asm_block(instrs, operands) + f'    report_e64("{lbl}", R, 1);\n'
    else:
        operands = f'[R]"r"(R),[vl]"r"({avl}UL)'
        instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", "li t1,0x5a5a", "vmv.s.x v24,t1",
                  f"vse{s}.v v24,(%[R])"]
        lbl = f"vmv.s.x e{s} {lmul}"
        return asm_block(instrs, operands) + f'    {dump_w(s)}("{lbl}", R, 1);\n'


def emit_slide(mn, form, sew, lmul):
    """vslideup/down .vx/.vi, vslide1up/down .vx (scalar inject)."""
    s = sew; avl = avl_for(s, lmul)
    operands = f'[A]"r"(A),[R]"r"(R),[vl]"r"({avl}UL)'
    if form == "vx":
        op = f"{mn}.vx v24,v8,t1"; scal = ["li t1,3"]
    elif form == "vi":
        op = f"{mn}.vi v24,v8,3"; scal = []
    else:  # 1up/1down vx scalar inject
        op = f"{mn}.vx v24,v8,t1"; scal = ["li t1,777"]
    # preload v24 so slid-in (undisturbed) region is deterministic
    instrs = ([f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", f"vle{s}.v v24,(%[A])",
               f"vle{s}.v v8,(%[A])"] + scal + [op, f"vse{s}.v v24,(%[R])"])
    lbl = f"{mn}.{form} e{s} {lmul} avl={avl}"
    return asm_block(instrs, operands) + f'    {dump_w(s)}("{lbl}", R, {avl});\n'


def emit_fp_slide(mn, sew, lmul):
    s = sew; avl = avl_for(s, lmul)
    operands = f'[A]"r"(FA{s}),[B]"r"(FB{s}),[R]"r"(R),[vl]"r"({avl}UL)'
    instrs = [f"vsetvli t0,%[vl],e{s},{lmul},ta,ma", f"{FL[s]} ft0,0(%[B])",
              f"vle{s}.v v24,(%[A])", f"vle{s}.v v8,(%[A])",
              f"{mn}.vf v24,v8,ft0", f"vse{s}.v v24,(%[R])"]
    lbl = f"{mn}.vf e{s} {lmul} avl={avl}"
    return asm_block(instrs, operands, '"t0","ft0","memory"') + f'    {dump_w(s)}("{lbl}", R, {avl});\n'


def emit_blocked_probe(mn, form):
    """issue an op AraXL is expected to reject (illegal trap); Spike executes it.
    The differential shows Verilator BLOCKED while Spike produces a result."""
    avl = 16
    if mn == "vrgatherei16":
        operands = '[A]"r"(A),[B]"r"(B),[R]"r"(R),[vl]"r"(%dUL)' % avl
        instrs = ["vsetvli t0,%[vl],e32,m1,ta,ma", "vle32.v v8,(%[A])",
                  "vle16.v v16,(%[B])", "vrgatherei16.vv v24,v8,v16", "vse32.v v24,(%[R])"]
        lbl = "vrgatherei16.vv e32 m1"
    else:  # vcompress.vm
        operands = '[A]"r"(A),[M]"r"(M),[R]"r"(R),[vl]"r"(%dUL)' % avl
        instrs = ["vsetvli t0,%[vl],e32,m1,ta,ma", "vlm.v v0,(%[M])",
                  "vle32.v v8,(%[A])", "vcompress.vm v24,v8,v0", "vse32.v v24,(%[R])"]
        lbl = "vcompress.vm e32 m1"
    return asm_block(instrs, operands) + f'    report_e32("{lbl}", R, {avl});\n'


def emit_whole_mv(mn):
    """vmvNr.v whole-register move. Dump only the first 8 e32 elements (identical
    element-wise on both VLENs, so VLEN-independent)."""
    operands = '[A]"r"(A),[R]"r"(R),[vl]"r"(8UL)'
    instrs = ["vsetvli t0,%[vl],e32,m1,ta,ma", "vle32.v v8,(%[A])",
              f"{mn} v24,v8", "vse32.v v24,(%[R])"]
    lbl = f"{mn} (first 8 e32 elems)"
    return asm_block(instrs, operands) + f'    report_e32("{lbl}", R, 8);\n'


def emit_cfg(mn):
    """vsetvli/vsetivli/vsetvl: set a vtype with avl < VLMAX_spike so vl==avl on
    both sims; dump vl and vtype (both VLEN-independent for this avl)."""
    out = []
    configs = [("e8", "m1", 20), ("e32", "m1", 17), ("e64", "m2", 30), ("e16", "mf2", 10)]
    for ew, lm, avl in configs:
        if mn == "vsetivli":
            avl = min(avl, 31)
            instrs = [f"vsetivli t1,{avl},{ew},{lm},ta,ma", "csrr t2,0xC20", "sd t1,0(%[R])",
                      "csrr t2,0xC21", "sd t2,8(%[R])"]
        elif mn == "vsetvl":
            # set vtype via vsetvli to capture its encoding, then exercise the
            # register-form vsetvl with that vtype value.
            instrs = [f"vsetvli t5,%[avl],{ew},{lm},ta,ma", "csrr t4,0xC21",
                      "vsetvl t1,%[avl],t4", "sd t1,0(%[R])", "csrr t2,0xC21", "sd t2,8(%[R])"]
        else:  # vsetvli
            instrs = [f"vsetvli t1,%[avl],{ew},{lm},ta,ma", "sd t1,0(%[R])",
                      "csrr t2,0xC21", "sd t2,8(%[R])"]
        operands = '[R]"r"(R),[avl]"r"(%dUL)' % avl
        lbl = f"{mn} {ew} {lm} avl={avl} -> [vl,vtype]"
        out.append(asm_block(instrs, operands, '"t1","t2","t3","t4","t5","memory"')
                   + f'    report_e64("{lbl}", R, 2);\n')
    return out


def _eew(mn):
    for e in (64, 32, 16, 8):
        if str(e) in mn:
            return e
    return 32


def emit_mem_unit(mn):
    """vle<e>.v / vse<e>.v round-trip (load A -> store R), or vlm/vsm, or vle*ff (blocked)."""
    if "ff" in mn:   # fault-only-first: AraXL illegal
        e = _eew(mn); avl = avl_for(e, "m1")
        operands = f'[A]"r"(A),[R]"r"(R),[vl]"r"({avl}UL)'
        instrs = [f"vsetvli t0,%[vl],e{e},m1,ta,ma", f"{mn} v8,(%[A])", f"vse{e}.v v8,(%[R])"]
        return asm_block(instrs, operands) + f'    {dump_w(e)}("{mn} m1 avl={avl}", R, {avl});\n'
    if mn in ("vlm.v", "vsm.v"):
        avl = 64
        operands = '[A]"r"(A),[R]"r"(R),[vl]"r"(%dUL)' % avl
        instrs = [f"vsetvli t0,%[vl],e8,m1,ta,ma", "vlm.v v8,(%[A])", "vsm.v v8,(%[R])"]
        return asm_block(instrs, operands) + f'    report_bytes("{mn} vl={avl}", R, {avl // 8});\n'
    e = _eew(mn); avl = avl_for(e, "m1")
    operands = f'[A]"r"(A),[R]"r"(R),[vl]"r"({avl}UL)'
    instrs = [f"vsetvli t0,%[vl],e{e},m1,ta,ma", f"vle{e}.v v8,(%[A])", f"vse{e}.v v8,(%[R])"]
    return asm_block(instrs, operands) + f'    {dump_w(e)}("{mn} m1 avl={avl} (unit ld/st round-trip)", R, {avl});\n'


def emit_mem_strided(mn):
    """vlse (strided load) or vsse (strided store) round-trip; stride = 2*eew bytes.
    Strided stores write element-scattered (non-64B-aligned) addresses, which is
    where AraXL is known to deadlock -> expect FAIL_HANG there."""
    e = _eew(mn); avl = min(avl_for(e, "m1"), 24); stride = 2 * (e // 8)
    operands = f'[A]"r"(A),[R]"r"(R),[D]"r"(D0),[vl]"r"({avl}UL),[st]"r"({stride}UL)'
    if mn.startswith("vls"):   # strided load
        instrs = [f"vsetvli t0,%[vl],e{e},m1,ta,ma", f"vlse{e}.v v8,(%[A]),%[st]",
                  f"vse{e}.v v8,(%[R])"]
        lbl = f"{mn} m1 avl={avl} stride={stride}B"
    else:                       # strided store: store strided to R, read back strided to D0
        instrs = [f"vsetvli t0,%[vl],e{e},m1,ta,ma", f"vle{e}.v v8,(%[A])",
                  f"vsse{e}.v v8,(%[R]),%[st]", f"vlse{e}.v v16,(%[R]),%[st]",
                  f"vse{e}.v v16,(%[D])"]
        lbl = f"{mn} m1 avl={avl} stride={stride}B"
    tgt = "R" if mn.startswith("vls") else "D0"
    return asm_block(instrs, operands) + f'    {dump_w(e)}("{lbl}", {tgt}, {avl});\n'


def emit_mem_indexed(mn):
    """vluxei/vloxei (indexed load) or vsuxei/vsoxei (indexed store). The index
    vector (byte offsets, reversed, in-bounds) is filled by SCALAR code and loaded
    via vle - NOT built on-hardware with vid (vid is broken on AraXL, which would
    contaminate the result). Indexed scatter/scatter is a known AraXL hang risk."""
    e = _eew(mn); avl = min(avl_for(e, "m1"), 24); eb = e // 8
    fillc = (f'    for (int _i = 0; _i < {avl}; _i++) '
             f'((uint{e}_t *)IDX)[_i] = (uint{e}_t)(({avl} - 1 - _i) * {eb});\n')
    operands = f'[A]"r"(A),[I]"r"(IDX),[R]"r"(R),[D]"r"(D0),[vl]"r"({avl}UL)'
    if mn.startswith("vl"):     # indexed load
        instrs = [f"vsetvli t0,%[vl],e{e},m1,ta,ma", f"vle{e}.v v16,(%[I])",
                  f"{mn} v8,(%[A]),v16", f"vse{e}.v v8,(%[R])"]
        tgt = "R"
    else:                        # indexed store: scatter to R, gather back to D0
        ld = mn.replace("vsux", "vlux").replace("vsox", "vlox")
        instrs = [f"vsetvli t0,%[vl],e{e},m1,ta,ma", f"vle{e}.v v16,(%[I])",
                  f"vle{e}.v v8,(%[A])", f"{mn} v8,(%[R]),v16",
                  f"{ld} v24,(%[R]),v16", f"vse{e}.v v24,(%[D])"]
        tgt = "D0"
    return fillc + asm_block(instrs, operands) + f'    {dump_w(e)}("{mn} m1 avl={avl}", {tgt}, {avl});\n'


def emit_mem_whole(mn):
    """vlNre / vsNr whole-register load/store; dump first 8 e32 elems (VLEN-safe)."""
    operands = '[A]"r"(A),[R]"r"(R),[vl]"r"(8UL)'
    if mn.startswith("vl"):
        instrs = [f"{mn} v8,(%[A])", "vsetivli t0,8,e32,m1,ta,ma", "vse32.v v8,(%[R])"]
    else:  # vsNr.v store: load whole then store whole, read back prefix
        instrs = ["vl1re32.v v8,(%[A])", f"{mn} v8,(%[R])",
                  "vsetivli t0,8,e32,m1,ta,ma", "vle32.v v16,(%[R])", "vse32.v v16,(%[R])"]
    return asm_block(instrs, operands) + f'    report_e32("{mn} (first 8 e32)", R, 8);\n'


def emit_mem_segment(mn):
    """segment load/store: AraXL silently mis-decodes (nf ignored) -> expect
    FAIL_INCORRECT, except *ff segment which traps illegal -> BLOCKED."""
    e = _eew(mn); avl = 16; eb = e // 8
    operands = f'[A]"r"(A),[R]"r"(R),[I]"r"(IDX),[st]"r"({2 * eb}UL),[vl]"r"({avl}UL)'
    base = f"vsetvli t0,%[vl],e{e},m1,ta,ma"
    fillc = ""
    if "ff" in mn:               # fault-only-first segment load (illegal on AraXL)
        instrs = [base, f"{mn} v8,(%[A])", f"vse{e}.v v8,(%[R])"]
    elif mn.startswith("vlsseg"):   # STRIDED segment load
        instrs = [base, f"{mn} v8,(%[A]),%[st]", f"vse{e}.v v8,(%[R])"]
    elif mn.startswith("vssseg"):   # STRIDED segment store
        instrs = [base, f"vle{e}.v v8,(%[A])", f"{mn} v8,(%[R]),%[st]"]
    elif "ux" in mn or "ox" in mn:  # indexed segment (load or store); scalar-filled indices
        fillc = (f'    for (int _i = 0; _i < {avl}; _i++) '
                 f'((uint{e}_t *)IDX)[_i] = (uint{e}_t)(_i * {eb});\n')
        if mn.startswith("vl"):
            instrs = [base, f"vle{e}.v v16,(%[I])", f"{mn} v8,(%[A]),v16", f"vse{e}.v v8,(%[R])"]
        else:
            instrs = [base, f"vle{e}.v v16,(%[I])", f"vle{e}.v v8,(%[A])", f"{mn} v8,(%[R]),v16"]
    elif mn.startswith("vsseg"):    # unit-stride segment STORE
        instrs = [base, f"vle{e}.v v8,(%[A])", f"{mn} v8,(%[R])"]
    else:                            # unit-stride segment LOAD (vlsegNe)
        instrs = [base, f"{mn} v8,(%[A])", f"vse{e}.v v8,(%[R])"]
    return fillc + asm_block(instrs, operands) + f'    {dump_w(e)}("{mn} m1 avl={avl}", R, {avl});\n'


# ===========================================================================
# RV64 scalar emitters. Each kernel runs the instruction on a few fixed operand
# sets and reports results; differential vs Spike. frm pinned to RNE for FP.
# Operand vectors chosen to include pos/neg/zero/extreme values.
INT_OPS_A = ["0x0123456789ABCDEF", "0xFFFFFFFFFFFFFFFF", "0x8000000000000000",
             "0x000000007FFFFFFF", "42", "-1"]
INT_OPS_B = ["0x55AA55AA55AA55AA", "1", "0xFFFFFFFFFFFFFFFF",
             "0x0000000080000000", "-7", "0x40"]
SHAMTS = ["0", "1", "31", "63", "7", "20"]


def _scalar_kernel(mn, lines, n, fp=False):
    setfrm = '    asm volatile("fsrmi 0");\n' if fp else ""
    body = setfrm + "".join(lines)
    return body + f'    report_e64("{mn}", R, {n});\n'


def emit_scalar_rr(mn, word):
    lines, n = [], 0
    isshift = any(mn.startswith(p) for p in ("sll", "srl", "sra"))
    B = SHAMTS if isshift else INT_OPS_B
    for i in range(len(INT_OPS_A)):
        lines.append(f'    asm volatile("{mn} %0,%1,%2":"=r"(o):"r"({INT_OPS_A[i]}L),"r"({B[i]}L));'
                     f' R[{n}]=(uint64_t)o;\n'); n += 1
    return _scalar_kernel(mn, ["    long o;\n"] + lines, n)


def emit_scalar_imm(mn, word):
    lines, n = [], 0
    isshift = any(s in mn for s in ("slli", "srli", "srai"))
    imms = ["0", "1", "31", "20", "5", "12"] if isshift else ["0", "1", "-1", "2047", "-2048", "100"]
    for i in range(len(INT_OPS_A)):
        lines.append(f'    asm volatile("{mn} %0,%1,{imms[i]}":"=r"(o):"r"({INT_OPS_A[i]}L));'
                     f' R[{n}]=(uint64_t)o;\n'); n += 1
    return _scalar_kernel(mn, ["    long o;\n"] + lines, n)


def emit_scalar_u(mn):
    # lui: absolute immediate (layout-independent). auipc: PC-relative, so we take
    # the DIFFERENCE of two adjacent auipc - the PC cancels, leaving imm<<12 minus
    # the fixed instruction distance -> identical on both link layouts.
    lines, n = ["    long o, o2; (void)o2;\n"], 0
    for imm in ["0", "1", "0xFFFFF", "0x80000", "0x12345"]:
        if mn == "auipc":
            lines.append(f'    asm volatile("auipc %0,{imm}\\n auipc %1,0\\n sub %0,%0,%1"'
                         f':"=r"(o),"=r"(o2)); R[{n}]=(uint64_t)o;\n')
        else:
            lines.append(f'    asm volatile("lui %0,{imm}":"=r"(o)); R[{n}]=(uint64_t)o;\n')
        n += 1
    return _scalar_kernel(mn, lines, n)


def emit_scalar_load(mn):
    # load from MEM (known bytes) at a few offsets
    lines, n = ["    long o;\n"], 0
    for off in ["0", "8", "16", "24", "32"]:
        lines.append(f'    asm volatile("{mn} %0,{off}(%1)":"=r"(o):"r"(MEM)); R[{n}]=(uint64_t)o;\n'); n += 1
    return _scalar_kernel(mn, lines, n)


def emit_scalar_store(mn):
    sz = {"sb": "0xFF", "sh": "0xFFFF", "sw": "0xFFFFFFFF", "sd": "0xFFFFFFFFFFFFFFFF"}[mn]
    lines = ["    long o;\n",
             '    for (int i=0;i<64;i++) ((volatile uint64_t*)MEM)[i]=0;\n']
    n = 0
    for i, val in enumerate(["0x1122334455667788", "0xFFFFFFFFFFFFFFFF", "0x00000000DEADBEEF"]):
        off = i * 8
        lines.append(f'    asm volatile("{mn} %0,{off}(%1)"::"r"({val}L),"r"(MEM):"memory");\n')
        lines.append(f'    asm volatile("ld %0,{off}(%1)":"=r"(o):"r"(MEM)); R[{n}]=(uint64_t)o & {sz}ULL;\n'); n += 1
    return _scalar_kernel(mn, lines, n)


def emit_scalar_branch(mn):
    lines = ["    long o;\n"]; n = 0
    pairs = [("5", "5"), ("5", "6"), ("-1", "1"), ("0", "0"), ("-5", "-6")]
    for i, (a, b) in enumerate(pairs):
        lines.append(f'    asm volatile("{mn} %1,%2,1f\\n li %0,0\\n j 2f\\n 1: li %0,1\\n 2:":'
                     f'"=r"(o):"r"({a}L),"r"({b}L)); R[{n}]=(uint64_t)o;\n'); n += 1
    return _scalar_kernel(mn, lines, n)


def emit_scalar_fp(mn):
    # FP reg-reg/unary; load operands from FP const pools, store result bits
    w = 64 if mn.endswith(".d") else 32
    fl = "fld" if w == 64 else "flw"
    fs = "fsd" if w == 64 else "fsw"
    pa, pb = f"FA{w}", f"FB{w}"
    unary = mn.startswith("fsqrt")
    lines = ["    long o; (void)o;\n"]
    n = 0
    for i in range(5):
        if unary:
            ld = f'    asm volatile("fsrmi 0\\n {fl} ft0,{i*8}(%[a])\\n {mn} ft1,ft0\\n {fs} ft1,0(%[r])"::[a]"r"({pa}),[r]"r"(&R[{n}]):"ft0","ft1","memory");\n'
        else:
            ld = f'    asm volatile("fsrmi 0\\n {fl} ft0,{i*8}(%[a])\\n {fl} ft1,{i*8}(%[b])\\n {mn} ft2,ft0,ft1\\n {fs} ft2,0(%[r])"::[a]"r"({pa}),[b]"r"({pb}),[r]"r"(&R[{n}]):"ft0","ft1","ft2","memory");\n'
        lines.append(ld); n += 1
    return "".join(lines) + f'    report_e64("{mn}", R, {n});\n'


def emit_scalar_fma(mn):
    w = 64 if mn.endswith(".d") else 32
    fl = "fld" if w == 64 else "flw"
    fs = "fsd" if w == 64 else "fsw"
    lines = []
    n = 0
    for i in range(5):
        lines.append(f'    asm volatile("fsrmi 0\\n {fl} ft0,{i*8}(%[a])\\n {fl} ft1,{i*8}(%[b])\\n {fl} ft2,{i*8}(%[c])\\n {mn} ft3,ft0,ft1,ft2\\n {fs} ft3,0(%[r])"::[a]"r"(FA{w}),[b]"r"(FB{w}),[c]"r"(FC{w}),[r]"r"(&R[{n}]):"ft0","ft1","ft2","ft3","memory");\n'); n += 1
    return "".join(lines) + f'    report_e64("{mn}", R, {n});\n'


def emit_scalar_fcvt_cmp(mn):
    # fcvt.*/fcmp/fclass/fmv : mixed src/dst types. Use a generic 1-src or 2-src
    # form storing an xlen result. Heuristic by mnemonic.
    lines = ["    long o; double dd; float ff; (void)dd;(void)ff;\n"]
    n = 0
    # fmv.w.x / fmv.d.x move an INTEGER (x reg) bit pattern into an f reg
    if mn in ("fmv.w.x", "fmv.d.x"):
        fs = "fsd" if mn == "fmv.d.x" else "fsw"
        for i in range(5):
            lines.append(f'    asm volatile("{mn} ft0,%1\\n {fs} ft0,0(%[r])"::[r]"r"(&R[{i}]),'
                         f'"r"({INT_OPS_A[i]}L):"ft0","memory");\n'); n += 1
        return "".join(lines) + f'    report_e64("{mn}", R, {n});\n'
    fp_to_int = any(mn.startswith(p) for p in ("fcvt.w", "fcvt.l", "fcvt.wu", "fcvt.lu",
                                               "feq", "flt", "fle", "fclass", "fmv.x"))
    src_w = 64 if (".d" in mn) else 32
    fl = "fld" if src_w == 64 else "flw"
    for i in range(5):
        if mn in ("feq.s", "flt.s", "fle.s", "feq.d", "flt.d", "fle.d"):
            l = f'    asm volatile("fsrmi 0\\n {fl} ft0,{i*8}(%[a])\\n {fl} ft1,{i*8}(%[b])\\n {mn} %0,ft0,ft1":"=r"(o):[a]"r"(FA{src_w}),[b]"r"(FB{src_w}):"ft0","ft1"); R[{n}]=(uint64_t)o;\n'
        elif fp_to_int:
            l = f'    asm volatile("fsrmi 0\\n {fl} ft0,{i*8}(%[a])\\n {mn} %0,ft0":"=r"(o):[a]"r"(FA{src_w}):"ft0"); R[{n}]=(uint64_t)o;\n'
        else:
            # int->fp or fp->fp: produce fp, store bits
            dst_w = 64 if mn.split(".")[1] in ("d", "l", "lu") or mn.endswith(".d") else 32
            fs = "fsd" if dst_w == 64 else "fsw"
            if mn.startswith("fcvt") and ("." in mn) and mn.split(".")[2:] and mn.split(".")[2] in ("w", "wu", "l", "lu"):
                # int source in x reg
                l = f'    asm volatile("fsrmi 0\\n {mn} ft0,%1\\n {fs} ft0,0(%[r])"::[r]"r"(&R[{n}]),"r"({INT_OPS_A[i]}L):"ft0","memory"); o=0;\n'
            else:
                l = f'    asm volatile("fsrmi 0\\n {fl} ft0,{i*8}(%[a])\\n {mn} ft1,ft0\\n {fs} ft1,0(%[r])"::[a]"r"(FA{src_w}),[r]"r"(&R[{n}]):"ft0","ft1","memory"); o=0;\n'
        lines.append(l); n += 1
    return "".join(lines) + f'    report_e64("{mn}", R, {n});\n'


def emit_scalar_amo(mn):
    w = 64 if mn.endswith(".d") else 32
    lines = ['    long o;\n', '    ((volatile uint64_t*)MEM)[0]=0x0F0F0F0F0F0F0F0FULL;\n']
    n = 0
    for val in ["0x11111111", "0xFFFFFFFF", "0x80000000"]:
        lines.append(f'    asm volatile("{mn} %0,%2,(%1)":"=r"(o):"r"(MEM),"r"({val}L):"memory"); R[{n}]=(uint64_t)o;\n'); n += 1
        lines.append(f'    R[{n}]=((volatile uint64_t*)MEM)[0];\n'); n += 1
    return _scalar_kernel(mn, lines, n)


def emit_scalar_csr(mn):
    # exercise on fcsr (0x003) - read/write, deterministic
    lines = ["    long o;\n", '    asm volatile("csrw fcsr,zero");\n']
    n = 0
    args = ["7", "0", "0xFF"] if not mn.endswith("i") else ["7", "0", "31"]
    for a in args:
        if mn.endswith("i"):
            imm = min(int(a, 0), 31)
            lines.append(f'    asm volatile("csrw fcsr,zero\\n {mn} %0,fcsr,{imm}":"=r"(o)); R[{n}]=(uint64_t)o;\n'); n += 1
        else:
            lines.append(f'    asm volatile("csrw fcsr,zero\\n {mn} %0,fcsr,%1":"=r"(o):"r"({a}L)); R[{n}]=(uint64_t)o;\n'); n += 1
        lines.append(f'    {{long f; asm volatile("csrr %0,fcsr":"=r"(f)); R[{n}]=(uint64_t)f;}}\n'); n += 1
    return _scalar_kernel(mn, lines, n)


# ---------------------------------------------------------------------------
def build_variants(entry):
    """return list of (emit_fn_call_string) for one instruction."""
    g = entry["group"]; mn = entry["mnemonic"]; forms = entry["forms"]; sews = entry["sew"]
    out = []
    s0 = 32 if 32 in sews else (sews[0] if sews else 32)
    reads_vd = (g == "rvv-int-muladd")

    if g == "rvv-int-cmp":
        for s in sews:
            out.append(emit_cmp(mn, forms[0], s, "m1"))
        for f in forms[1:]:
            out.append(emit_cmp(mn, f, s0, "m1"))
        for lm in ("m2", "m8"):
            out.append(emit_cmp(mn, forms[0], s0, lm))
        return out
    if g == "rvv-int-widen":
        prim = forms[0]
        for s in sews:
            if lmul_ok(s, "m1"):
                out.append(emit_widen(mn, prim, s, "m1"))
        for f in forms[1:]:
            out.append(emit_widen(mn, f, s0, "m1"))
        if lmul_ok(s0, "m2"):
            out.append(emit_widen(mn, prim, s0, "m2"))
        return out
    if g == "rvv-int-narrow":
        for s in sews:                       # sew = source/wide width
            if s // 2 >= 8 and lmul_ok(s // 2, "m1"):
                out.append(emit_narrow(mn, forms[0], s, "m1"))
        for f in forms[1:]:
            out.append(emit_narrow(mn, f, s0 if s0 in sews else sews[0], "m1"))
        return out
    if g == "rvv-int-ext":
        for f in forms:
            out.append(emit_ext(mn, f, "m1"))
        return out
    if g == "rvv-int-merge":
        for s in sews:
            out.append(emit_merge(mn, forms[0], s, "m1"))
        for f in forms[1:]:
            out.append(emit_merge(mn, f, s0, "m1"))
        for lm in ("m2", "m8"):
            out.append(emit_merge(mn, forms[0], s0, lm))
        return out
    if g == "rvv-int-carry":
        for s in sews:
            out.append(emit_carry(mn, forms[0], s, "m1"))
        for f in forms[1:]:
            out.append(emit_carry(mn, f, s0, "m1"))
        out.append(emit_carry(mn, forms[0], s0, "m2"))
        return out

    # ---- floating-point classes ----
    fs0 = 32 if 32 in sews else (sews[0] if sews else 32)
    if g in ("rvv-fp-arith", "rvv-fp-muladd", "rvv-fp-minmax", "rvv-fp-sgnj"):
        rv = (g == "rvv-fp-muladd")
        for s in sews:
            out.append(emit_fp(mn, forms[0], s, "m1", rv))
        for f in forms[1:]:
            out.append(emit_fp(mn, f, fs0, "m1", rv))
        for lm in ("m2", "m8"):
            out.append(emit_fp(mn, forms[0], fs0, lm, rv))
        return out
    if g == "rvv-fp-unary":
        for s in sews:
            out.append(emit_fp_unary(mn, s, "m1"))
        out.append(emit_fp_unary(mn, fs0, "m2"))
        return out
    if g == "rvv-fp-cmp":
        for s in sews:
            out.append(emit_fp_cmp(mn, forms[0], s, "m1"))
        for f in forms[1:]:
            out.append(emit_fp_cmp(mn, f, fs0, "m1"))
        return out
    if g == "rvv-fp-merge":
        for s in sews:
            out.append(emit_fp_merge(mn, forms[0], s, "m1"))
        return out
    if g == "rvv-fp-scalar":
        for s in sews:
            out.append(emit_fp_scalar(mn, s, "m1"))
        return out
    if g == "rvv-fp-widen":
        for s in sews:
            if lmul_ok(s, "m1"):
                out.append(emit_fp_widen(mn, forms[0], s, "m1"))
        for f in forms[1:]:
            out.append(emit_fp_widen(mn, f, fs0 if fs0 in sews else sews[0], "m1"))
        return out
    if g == "rvv-fp-cvt":
        # vfcvt: same width {16,32,64}. vfwcvt: src {16,32} -> 2x. vfncvt: this
        # emit uses src=2*sew, so valid sew (the narrow/base) is {16,32} (no FP128).
        cvt_sews = {"vfcvt": [16, 32, 64], "vfwcvt": [16, 32], "vfncvt": [16, 32]}[mn]
        for suf in forms:
            for s in cvt_sews:
                out.append(emit_fp_cvt(mn, suf, s, "m1"))
        return out

    # ---- reductions ----
    if g in ("rvv-red-int", "rvv-red-fp"):
        fp = (g == "rvv-red-fp")
        widen = mn.startswith("vw") or mn.startswith("vfw")
        for s in sews:
            if widen:
                if lmul_ok(s, "m1"):
                    out.append(emit_red_w(mn, s, "m1", fp))
            else:
                out.append(emit_red(mn, s, "m1", fp))
        # a couple LMULs at s0 to characterize the vredsum-LMUL finding
        for lm in ("m2", "m4", "m8"):
            if not widen and lmul_ok(s0, lm):
                out.append(emit_red(mn, s0, lm, fp))
        return out

    # ---- mask ----
    if g == "rvv-mask-logical":
        for lm in ("m1", "m2", "m8"):
            out.append(emit_mask_logical(mn, lm))
        return out
    if g == "rvv-mask-pop":
        for lm in ("m1", "m2", "m8"):
            out.append(emit_mask_pop(mn, lm))
        return out
    if g == "rvv-mask-set":
        for lm in ("m1", "m2"):
            out.append(emit_mask_set(mn, lm))
        return out
    if g == "rvv-mask-iota":
        for s in sews:
            out.append(emit_iota(mn, s, "m1"))
        for lm in ("m2", "m8"):
            out.append(emit_iota(mn, s0, lm))
        return out
    if g == "rvv-mask-xmv":
        for s in sews:
            out.append(emit_xmv(mn, s, "m1"))
        return out

    # ---- permutation (mixed: int slides, fp slides, blocked gather/compress, whole-reg) ----
    if g == "rvv-perm":
        if mn in ("vslideup", "vslidedown"):
            for s in sews:
                out.append(emit_slide(mn, "vx", s, "m1"))
            out.append(emit_slide(mn, "vi", s0, "m1"))
            out.append(emit_slide(mn, "vx", s0, "m2"))
            return out
        if mn in ("vslide1up", "vslide1down"):
            for s in sews:
                out.append(emit_slide(mn, "vx", s, "m1"))
            return out
        if mn in ("vfslide1up", "vfslide1down"):
            for s in sews:
                out.append(emit_fp_slide(mn, s, "m1"))
            return out
        if mn in ("vrgatherei16", "vcompress"):
            out.append(emit_blocked_probe(mn, forms[0]))
            return out
        if mn.startswith("vmv") and mn.endswith("r.v"):
            out.append(emit_whole_mv(mn))
            return out
        return out   # vrgather hand-written

    # ---- config ----
    if g == "rvv-config":
        return emit_cfg(mn)

    # ---- RV64 scalar ----
    fmt = entry["format"]
    if g in ("rv64i-reg", "rv64m"):
        return [emit_scalar_rr(mn, False)]
    if g == "rv64i-word":
        return [emit_scalar_rr(mn, True) if fmt == "R" else emit_scalar_imm(mn, True)]
    if g == "rv64i-imm":
        if fmt == "U":
            return [emit_scalar_u(mn)]
        return [emit_scalar_imm(mn, False)]
    if g == "rv64i-load":
        return [emit_scalar_load(mn)]
    if g == "rv64i-store":
        return [emit_scalar_store(mn)]
    if g == "rv64i-branch":
        return [emit_scalar_branch(mn)]
    if g == "rv64a":
        if mn.startswith("amo"):
            return [emit_scalar_amo(mn)]
        return []   # lr/sc handled separately (note)
    if g == "zicsr":
        return [emit_scalar_csr(mn)]
    if g in ("rv64f-arith", "rv64d-arith"):
        return [emit_scalar_fp(mn)]
    if g in ("rv64f-fma", "rv64d-fma"):
        return [emit_scalar_fma(mn)]
    if g in ("rv64f-misc", "rv64d-misc"):
        if any(mn.startswith(p) for p in ("fsgnj", "fmin", "fmax")):
            return [emit_scalar_fp(mn)]
        return [emit_scalar_fcvt_cmp(mn)]
    if g in ("rv64f-cvt", "rv64d-cvt"):
        return [emit_scalar_fcvt_cmp(mn)]

    # ---- memory ----
    if g == "rvv-mem-unit":
        return [emit_mem_unit(mn)]
    if g == "rvv-mem-strided":
        return [emit_mem_strided(mn)]
    if g == "rvv-mem-indexed":
        return [emit_mem_indexed(mn)]
    if g == "rvv-mem-whole":
        return [emit_mem_whole(mn)]
    if g == "rvv-mem-segment":
        return [emit_mem_segment(mn)]

    # default "vec" kind (arith/logical/shift/minmax/mul/div/muladd/merge/carry-vec)
    prim = forms[0]
    for s in sews:
        out.append(emit_vec(mn, prim, s, "m1", False, False, reads_vd))
    for lm in ("m2", "m8", "mf2"):
        if lmul_ok(s0, lm):
            out.append(emit_vec(mn, prim, s0, lm, False, False, reads_vd))
    for f in forms[1:]:
        out.append(emit_vec(mn, f, s0, "m1", False, False, reads_vd))
    out.append(emit_vec(mn, prim, s0, "m1", True, False, reads_vd))   # masked
    out.append(emit_vec(mn, prim, s0, "m1", False, True, reads_vd))   # vl=0
    return out


HEADER = '''/* AUTO-GENERATED by flow/verif/scripts/gen_kernels.py - directed test for {mn}.
 * Differential vs Spike; per-variant #V blocks. Do not hand-edit; regenerate.
 * {note}
 */
#include "verif.h"

static uint8_t A[2048] L2BUF;
static uint8_t B[2048] L2BUF;
static uint8_t R[4096] L2BUF;
static uint8_t D0[2048] L2BUF;
static uint8_t M[256]  L2BUF;
static uint8_t IDX[512] L2BUF;   /* index vector for indexed load/store (filled per-kernel) */

static void fill(void) {{
    for (int i = 0; i < 2048; i++) {{
        A[i]  = (uint8_t)(i * 7u + 3u);
        B[i]  = (uint8_t)((i * 13u + 131u) | 1u);   /* nonzero (safe for divide) */
        D0[i] = (uint8_t)(0xC0u + i);
    }}
    for (int i = 0; i < 256; i++) M[i] = (uint8_t)(0xA5u ^ (i * 3u));
}}

int main(void) {{
    fill();
    VBEGIN();
{body}    VEND();
    return 0;
}}
'''


HEADER_FP = '''/* AUTO-GENERATED by flow/verif/scripts/gen_kernels.py - directed test for {mn}.
 * Differential vs Spike; per-variant #V blocks. FP inputs are curated values
 * stored as raw bit patterns (host -ffast-math cannot fold them); results dumped
 * as raw bits for bit-exact comparison. Do not hand-edit; regenerate.
 * {note}
 */
#include "verif.h"

{pools}static uint8_t R[4096] L2BUF;
static uint8_t M[256]  L2BUF;

static void fill(void) {{
    for (int i = 0; i < 256; i++) M[i] = (uint8_t)(0xA5u ^ (i * 3u));
}}

int main(void) {{
    fill();
    VBEGIN();
{body}    VEND();
    return 0;
}}
'''


HEADER_SCALAR = '''/* AUTO-GENERATED by flow/verif/scripts/gen_kernels.py - directed RV64 scalar test
 * for {mn}. Runs the instruction on fixed operand sets; differential vs Spike.
 * FP ops pin frm=RNE. Do not hand-edit; regenerate.
 * {note}
 */
#include "verif.h"

{pools}static uint64_t R[256] L2BUF;     /* scalar results */
static uint64_t MEM[64] L2BUF;    /* memory for loads/stores/atomics */

static void fill(void) {{
    for (int i = 0; i < 64; i++) MEM[i] = 0x1100u * i + 0x0123456789ABCDEFULL;
}}

int main(void) {{
    fill();
    VBEGIN();
{body}    VEND();
    return 0;
}}
'''


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    ap.add_argument("--inventory", default=os.path.join(root, "inventory", "inventory.json"))
    ap.add_argument("--kernels-dir", default=os.path.join(root, "kernels"))
    ap.add_argument("--groups", nargs="+", required=True,
                    help="inventory groups to generate (e.g. rvv-int-arith ...)")
    ap.add_argument("--skip-existing-handwritten", nargs="*", default=["vadd", "vmseq", "vredsum"],
                    help="mnemonics already hand-written; do not overwrite")
    args = ap.parse_args()

    inv = json.load(open(args.inventory))
    n = 0
    for e in inv:
        if e["group"] not in args.groups:
            continue
        if e["expected"] == "absent_ext":
            continue
        mn = e["mnemonic"]
        if mn in args.skip_existing_handwritten:
            continue
        try:
            variants = build_variants(e)
        except Exception as ex:
            print(f"  SKIP {mn}: generator error {ex}")
            continue
        if not variants:
            continue
        body = "\n".join(variants)
        # pick the right header by what the body references
        needs_fp = any(p in body for p in ("FA16", "FA32", "FA64", "FB16", "FB32",
                                           "FB64", "FC16", "FC32", "FC64"))
        is_scalar = e["group"].startswith("rv64") or e["group"] == "zicsr"
        if is_scalar:
            src = HEADER_SCALAR.format(mn=mn, note=e.get("note", ""), body=body,
                                       pools=fp_pools() if needs_fp else "")
        elif needs_fp:
            src = HEADER_FP.format(mn=mn, note=e.get("note", ""), body=body, pools=fp_pools())
        else:
            src = HEADER.format(mn=mn, note=e.get("note", ""), body=body)
        gdir = os.path.join(args.kernels_dir, e["group"])
        os.makedirs(gdir, exist_ok=True)
        safe = mn.replace(".", "_")
        open(os.path.join(gdir, safe + ".c"), "w").write(src)
        meta = dict(mnemonic=mn, group=e["group"], ext=e["ext"], expected=e["expected"],
                    variants=[], note=e.get("note", ""))
        json.dump(meta, open(os.path.join(gdir, safe + ".meta.json"), "w"), indent=2)
        n += 1
        print(f"  gen {e['group']}/{safe}.c ({len(variants)} variants)")
    print(f"generated {n} kernels for groups {args.groups}")


if __name__ == "__main__":
    main()
