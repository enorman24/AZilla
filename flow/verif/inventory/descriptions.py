#!/usr/bin/env python3
"""
descriptions.py - plain-English description per base mnemonic, for the human-
readable column in the verification summary. Emits descriptions.json
({mnemonic: text}) consumed by merge.py.

Regular families (memory by element width, atomics, fp converts) are handled by
rule; everything else is an explicit table. Run: python3 descriptions.py
"""
import json
import os
import re

# ---- explicit table for the arithmetic / logical / mask / etc. base mnemonics
EXPLICIT = {
    # RVV config
    "vsetvli": "set vector length & type (immediate vtype)",
    "vsetivli": "set vector length & type (immediate AVL & vtype)",
    "vsetvl": "set vector length & type (register vtype)",
    # RVV integer arithmetic / logical / shift
    "vadd": "vector integer add", "vsub": "vector integer subtract",
    "vrsub": "vector integer reverse subtract (rs - v)",
    "vand": "vector bitwise AND", "vor": "vector bitwise OR", "vxor": "vector bitwise XOR",
    "vsll": "vector logical shift left", "vsrl": "vector logical shift right",
    "vsra": "vector arithmetic shift right",
    "vnsrl": "vector narrowing logical shift right", "vnsra": "vector narrowing arithmetic shift right",
    "vmin": "vector signed minimum", "vminu": "vector unsigned minimum",
    "vmax": "vector signed maximum", "vmaxu": "vector unsigned maximum",
    # RVV integer compare -> mask
    "vmseq": "vector compare equal -> mask", "vmsne": "vector compare not-equal -> mask",
    "vmsltu": "vector compare less-than unsigned -> mask", "vmslt": "vector compare less-than signed -> mask",
    "vmsleu": "vector compare less-or-equal unsigned -> mask", "vmsle": "vector compare less-or-equal signed -> mask",
    "vmsgtu": "vector compare greater-than unsigned -> mask", "vmsgt": "vector compare greater-than signed -> mask",
    # merge / move / carry
    "vmerge": "vector merge two sources under mask", "vmv.v": "vector copy/splat (move)",
    "vadc": "vector add with carry-in", "vsbc": "vector subtract with borrow-in",
    "vmadc": "vector produce carry-out mask of add", "vmsbc": "vector produce borrow-out mask of subtract",
    "vzext": "vector zero-extend to wider element", "vsext": "vector sign-extend to wider element",
    # integer mul / div / mul-add
    "vmul": "vector integer multiply (low half)", "vmulh": "vector multiply high, signed",
    "vmulhu": "vector multiply high, unsigned", "vmulhsu": "vector multiply high, signed*unsigned",
    "vdivu": "vector unsigned divide", "vdiv": "vector signed divide",
    "vremu": "vector unsigned remainder", "vrem": "vector signed remainder",
    "vmacc": "vector multiply-accumulate (vd += vs1*vs2)", "vnmsac": "vector negate-multiply-subtract (vd -= vs1*vs2)",
    "vmadd": "vector multiply-add (vd = vs1*vd + vs2)", "vnmsub": "vector negate-multiply-subtract (vd = -(vs1*vd)+vs2)",
    # widening integer
    "vwmul": "vector widening multiply, signed", "vwmulu": "vector widening multiply, unsigned",
    "vwmulsu": "vector widening multiply, signed*unsigned",
    "vwmacc": "vector widening multiply-accumulate, signed", "vwmaccu": "vector widening multiply-accumulate, unsigned",
    "vwmaccsu": "vector widening multiply-accumulate, signed*unsigned", "vwmaccus": "vector widening multiply-accumulate, unsigned*signed",
    "vwaddu": "vector widening add, unsigned", "vwadd": "vector widening add, signed",
    "vwsubu": "vector widening subtract, unsigned", "vwsub": "vector widening subtract, signed",
    # fixed-point
    "vsaddu": "vector saturating add, unsigned", "vsadd": "vector saturating add, signed",
    "vssubu": "vector saturating subtract, unsigned", "vssub": "vector saturating subtract, signed",
    "vaaddu": "vector averaging add, unsigned (rounding)", "vaadd": "vector averaging add, signed (rounding)",
    "vasubu": "vector averaging subtract, unsigned", "vasub": "vector averaging subtract, signed",
    "vsmul": "vector fractional multiply with rounding & saturate",
    "vssrl": "vector scaling shift right, logical (rounding)", "vssra": "vector scaling shift right, arithmetic (rounding)",
    "vnclipu": "vector narrowing clip, unsigned (round+saturate)", "vnclip": "vector narrowing clip, signed (round+saturate)",
    # RVV floating-point
    "vfadd": "vector FP add", "vfsub": "vector FP subtract", "vfrsub": "vector FP reverse subtract",
    "vfmul": "vector FP multiply", "vfdiv": "vector FP divide", "vfrdiv": "vector FP reverse divide (f / v)",
    "vfmacc": "vector FP fused multiply-accumulate (vd += vs1*vs2)",
    "vfnmacc": "vector FP fused negate multiply-accumulate", "vfmsac": "vector FP fused multiply-subtract",
    "vfnmsac": "vector FP fused negate multiply-subtract", "vfmadd": "vector FP fused multiply-add (vd = vs1*vd + vs2)",
    "vfnmadd": "vector FP fused negate multiply-add", "vfmsub": "vector FP fused multiply-subtract (vd form)",
    "vfnmsub": "vector FP fused negate multiply-subtract (vd form)",
    "vfsqrt": "vector FP square root", "vfrsqrt7": "vector FP reciprocal-sqrt estimate (7-bit)",
    "vfrec7": "vector FP reciprocal estimate (7-bit)",
    "vfmin": "vector FP minimum", "vfmax": "vector FP maximum",
    "vfsgnj": "vector FP sign-inject (copy sign)", "vfsgnjn": "vector FP sign-inject negated",
    "vfsgnjx": "vector FP sign-inject XOR", "vfclass": "vector FP classify",
    "vmfeq": "vector FP compare equal -> mask", "vmfne": "vector FP compare not-equal -> mask",
    "vmflt": "vector FP compare less-than -> mask", "vmfle": "vector FP compare less-or-equal -> mask",
    "vmfgt": "vector FP compare greater-than -> mask", "vmfge": "vector FP compare greater-or-equal -> mask",
    "vfmerge": "vector FP merge under mask", "vfmv.v.f": "vector FP splat scalar to all elements",
    "vfcvt": "vector FP convert (same width, int<->fp)", "vfwcvt": "vector FP widening convert (->2x width)",
    "vfncvt": "vector FP narrowing convert (2x->1x width)",
    "vfwadd": "vector FP widening add", "vfwsub": "vector FP widening subtract",
    "vfwmul": "vector FP widening multiply", "vfwmacc": "vector FP widening multiply-accumulate",
    "vfwnmacc": "vector FP widening negate multiply-accumulate", "vfwmsac": "vector FP widening multiply-subtract",
    "vfwnmsac": "vector FP widening negate multiply-subtract",
    "vfmv.f.s": "extract FP element 0 to scalar f-register", "vfmv.s.f": "insert scalar f-register into element 0",
    "vfslide1up": "vector FP slide up by 1, inject scalar", "vfslide1down": "vector FP slide down by 1, inject scalar",
    # reductions
    "vredsum": "vector integer sum reduction", "vredand": "vector AND reduction", "vredor": "vector OR reduction",
    "vredxor": "vector XOR reduction", "vredminu": "vector unsigned min reduction", "vredmin": "vector signed min reduction",
    "vredmaxu": "vector unsigned max reduction", "vredmax": "vector signed max reduction",
    "vwredsumu": "vector widening unsigned sum reduction", "vwredsum": "vector widening signed sum reduction",
    "vfredosum": "vector FP ordered sum reduction", "vfredusum": "vector FP unordered sum reduction",
    "vfredmin": "vector FP min reduction", "vfredmax": "vector FP max reduction",
    "vfwredosum": "vector FP widening ordered sum reduction", "vfwredusum": "vector FP widening unordered sum reduction",
    # mask
    "vmand": "mask bitwise AND", "vmnand": "mask bitwise NAND", "vmandn": "mask AND-NOT (a & ~b)",
    "vmxor": "mask bitwise XOR", "vmor": "mask bitwise OR", "vmnor": "mask bitwise NOR",
    "vmorn": "mask OR-NOT (a | ~b)", "vmxnor": "mask bitwise XNOR",
    "vcpop.m": "count set bits in mask (population count)", "vfirst.m": "index of first set mask bit (-1 if none)",
    "vmsbf.m": "set-before-first mask bit", "vmsif.m": "set-including-first mask bit", "vmsof.m": "set-only-first mask bit",
    "viota.m": "prefix-sum (iota) over mask bits", "vid.v": "write element index (0,1,2,...) to each lane",
    "vmv.x.s": "extract element 0 to integer register", "vmv.s.x": "insert integer register into element 0",
    # permute
    "vslideup": "vector slide elements up by offset", "vslidedown": "vector slide elements down by offset",
    "vslide1up": "vector slide up by 1, inject scalar", "vslide1down": "vector slide down by 1, inject scalar",
    "vrgather": "vector gather / permute elements by index", "vrgatherei16": "vector gather with 16-bit indices",
    "vcompress": "vector compress active (masked) elements together",
    "vmv1r.v": "whole-register move, 1 register", "vmv2r.v": "whole-register move, 2 registers",
    "vmv4r.v": "whole-register move, 4 registers", "vmv8r.v": "whole-register move, 8 registers",
    # RVV memory non-width-parameterized
    "vlm.v": "vector mask load (1 bit/element)", "vsm.v": "vector mask store (1 bit/element)",
    # ---- RV64 scalar ----
    "add": "integer add", "addi": "integer add immediate", "sub": "integer subtract",
    "addw": "32-bit integer add (sign-extended)", "addiw": "32-bit add immediate", "subw": "32-bit subtract",
    "and": "bitwise AND", "andi": "bitwise AND immediate", "or": "bitwise OR", "ori": "bitwise OR immediate",
    "xor": "bitwise XOR", "xori": "bitwise XOR immediate",
    "sll": "shift left logical", "slli": "shift left logical immediate", "srl": "shift right logical",
    "srli": "shift right logical immediate", "sra": "shift right arithmetic", "srai": "shift right arithmetic immediate",
    "sllw": "32-bit shift left logical", "slliw": "32-bit shift left immediate", "srlw": "32-bit shift right logical",
    "srliw": "32-bit shift right logical immediate", "sraw": "32-bit shift right arithmetic", "sraiw": "32-bit shift right arithmetic immediate",
    "slt": "set-less-than, signed", "sltu": "set-less-than, unsigned", "slti": "set-less-than immediate, signed",
    "sltiu": "set-less-than immediate, unsigned",
    "lui": "load upper immediate", "auipc": "add upper immediate to PC",
    "lb": "load byte (sign-extend)", "lbu": "load byte unsigned", "lh": "load halfword (sign-extend)",
    "lhu": "load halfword unsigned", "lw": "load word (sign-extend)", "lwu": "load word unsigned", "ld": "load doubleword",
    "sb": "store byte", "sh": "store halfword", "sw": "store word", "sd": "store doubleword",
    "beq": "branch if equal", "bne": "branch if not equal", "blt": "branch if less-than signed",
    "bge": "branch if greater-or-equal signed", "bltu": "branch if less-than unsigned", "bgeu": "branch if greater-or-equal unsigned",
    "jal": "jump and link", "jalr": "jump and link register",
    "fence": "memory ordering fence", "fence.i": "instruction-fetch fence", "ecall": "environment call (trap)",
    "ebreak": "breakpoint (trap)", "c.*": "compressed (16-bit) instruction family (exercised by all compiled code)",
    "mul": "integer multiply (low)", "mulh": "multiply high, signed", "mulhsu": "multiply high, signed*unsigned",
    "mulhu": "multiply high, unsigned", "mulw": "32-bit multiply", "div": "signed divide", "divu": "unsigned divide",
    "divw": "32-bit signed divide", "divuw": "32-bit unsigned divide", "rem": "signed remainder", "remu": "unsigned remainder",
    "remw": "32-bit signed remainder", "remuw": "32-bit unsigned remainder",
    "lr.w": "load-reserved word (atomic)", "lr.d": "load-reserved doubleword", "sc.w": "store-conditional word", "sc.d": "store-conditional doubleword",
    "csrrw": "atomic read/write CSR", "csrrs": "atomic read & set CSR bits", "csrrc": "atomic read & clear CSR bits",
    "csrrwi": "atomic read/write CSR (immediate)", "csrrsi": "atomic read & set CSR bits (immediate)", "csrrci": "atomic read & clear CSR bits (immediate)",
    # scalar FP misc
    "fmv.x.w": "move FP bits to integer register (32-bit)", "fmv.w.x": "move integer bits to FP register (32-bit)",
    "fmv.x.d": "move FP bits to integer register (64-bit)", "fmv.d.x": "move integer bits to FP register (64-bit)",
}

# ---- family rules for the regular memory/amo/fp-convert mnemonics
def family(mn):
    # AMOs: amo<op>.<w|d>
    m = re.match(r"amo(\w+?)\.(w|d)$", mn)
    if m:
        op = {"add": "add", "and": "AND", "or": "OR", "xor": "XOR", "swap": "swap",
              "min": "min signed", "max": "max signed", "minu": "min unsigned", "maxu": "max unsigned"}.get(m.group(1), m.group(1))
        wd = "32-bit word" if m.group(2) == "w" else "64-bit doubleword"
        return f"atomic memory {op}, {wd}"
    # scalar FP arith/cmp/etc with .s/.d
    m = re.match(r"(f[a-z0-9]+)\.(s|d)$", mn)
    if m and not mn.startswith("fcvt") and not mn.startswith("fmv"):
        base = {"fadd": "FP add", "fsub": "FP subtract", "fmul": "FP multiply", "fdiv": "FP divide",
                "fsqrt": "FP square root", "fmadd": "FP fused multiply-add", "fmsub": "FP fused multiply-subtract",
                "fnmadd": "FP fused negate multiply-add", "fnmsub": "FP fused negate multiply-subtract",
                "fmin": "FP minimum", "fmax": "FP maximum", "fsgnj": "FP sign-inject (copy sign)",
                "fsgnjn": "FP sign-inject negated", "fsgnjx": "FP sign-inject XOR",
                "feq": "FP compare equal", "flt": "FP compare less-than", "fle": "FP compare less-or-equal",
                "fclass": "FP classify"}.get(m.group(1))
        prec = "single precision" if m.group(2) == "s" else "double precision"
        if base:
            return f"{base}, {prec}"
    # scalar FP loads/stores
    if mn in ("flw", "fld", "fsw", "fsd"):
        return {"flw": "load FP single from memory", "fld": "load FP double from memory",
                "fsw": "store FP single to memory", "fsd": "store FP double to memory"}[mn]
    # fcvt.<dst>.<src>
    m = re.match(r"fcvt\.(\w+)\.(\w+)$", mn)
    if m:
        ty = {"s": "FP single", "d": "FP double", "w": "32-bit signed int", "wu": "32-bit unsigned int",
              "l": "64-bit signed int", "lu": "64-bit unsigned int"}
        return f"convert {ty.get(m.group(2), m.group(2))} -> {ty.get(m.group(1), m.group(1))}"
    # RVV unit-stride load/store with element width: vle{N}.v / vse{N}.v (+ ff)
    m = re.match(r"v(l|s)e(\d+)(ff)?\.v$", mn)
    if m:
        d = "load" if m.group(1) == "l" else "store"
        ff = " (fault-only-first)" if m.group(3) else ""
        return f"vector unit-stride {d}, {m.group(2)}-bit elements{ff}"
    # strided: vlse{N}.v / vsse{N}.v
    m = re.match(r"v(l|s)se(\d+)\.v$", mn)
    if m:
        d = "load" if m.group(1) == "l" else "store"
        return f"vector strided {d}, {m.group(2)}-bit elements"
    # indexed: v(l|s)(ux|ox)ei{N}.v
    m = re.match(r"v(l|s)(ux|ox)ei(\d+)\.v$", mn)
    if m:
        d = "indexed-load (gather)" if m.group(1) == "l" else "indexed-store (scatter)"
        order = "unordered" if m.group(2) == "ux" else "ordered"
        return f"vector {d}, {order}, {m.group(3)}-bit indices"
    # whole-register load/store: vl{n}re{N}.v / vs{n}r.v
    m = re.match(r"vl(\d+)re(\d+)\.v$", mn)
    if m:
        return f"whole-register load, {m.group(1)} register(s)"
    m = re.match(r"vs(\d+)r\.v$", mn)
    if m:
        return f"whole-register store, {m.group(1)} register(s)"
    # segments: vlseg{n}e{N}(ff).v / vsseg / vlsseg / vssseg / v(l|s)(ux|ox)seg{n}ei{N}.v
    m = re.match(r"v(l|s)seg(\d+)e(\d+)(ff)?\.v$", mn)
    if m:
        d = "load" if m.group(1) == "l" else "store"
        ff = " (fault-only-first)" if m.group(4) else ""
        return f"vector unit-stride segment {d}, {m.group(2)} fields x {m.group(3)}-bit{ff}"
    m = re.match(r"v(l|s)sseg(\d+)e(\d+)\.v$", mn)
    if m:
        d = "load" if m.group(1) == "l" else "store"
        return f"vector strided segment {d}, {m.group(2)} fields x {m.group(3)}-bit"
    m = re.match(r"v(l|s)(ux|ox)seg(\d+)ei(\d+)\.v$", mn)
    if m:
        d = "indexed segment load" if m.group(1) == "l" else "indexed segment store"
        order = "unordered" if m.group(2) == "ux" else "ordered"
        return f"vector {d}, {order}, {m.group(3)} fields, {m.group(4)}-bit indices"
    return None


def describe(mn):
    if mn in EXPLICIT:
        return EXPLICIT[mn]
    f = family(mn)
    return f if f else ""


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    inv = json.load(open(os.path.join(here, "inventory.json")))
    out, missing = {}, []
    for e in inv:
        mn = e["mnemonic"]
        if e["expected"] == "absent_ext":
            continue
        d = describe(mn)
        out[mn] = d
        if not d:
            missing.append(mn)
    json.dump(out, open(os.path.join(here, "descriptions.json"), "w"), indent=1, sort_keys=True)
    print(f"wrote descriptions.json: {len(out)} mnemonics, {len(missing)} missing")
    if missing:
        print("  MISSING:", ", ".join(missing))


if __name__ == "__main__":
    main()
