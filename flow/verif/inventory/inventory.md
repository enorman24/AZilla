# Instruction inventory (RVV 1.0 + RV64 scalar)

- Total base mnemonics: **400** (RVV 236, RV64 164)
- expected `absent_ext`: 7
- expected `blocked_illegal`: 10
- expected `blocked_silent`: 24
- expected `supported`: 359

| Mnemonic | Ext | Group | Format | Forms | SEW | Expected | Note |
|---|---|---|---|---|---|---|---|
| `vsetvli` | RVV | rvv-config | vsetvli | x |  | supported | sets vl/vtype; exercised by every vector kernel |
| `vsetivli` | RVV | rvv-config | vsetivli | x |  | supported | immediate AVL form |
| `vsetvl` | RVV | rvv-config | vsetvl | x |  | supported | register vtype form |
| `vle8.v` | RVV | rvv-mem-unit | VL-unit | v | 8 | supported | unit-stride load (extraction primitive: verify early) |
| `vse8.v` | RVV | rvv-mem-unit | VS-unit | v | 8 | supported | unit-stride store (extraction primitive: verify early) |
| `vle16.v` | RVV | rvv-mem-unit | VL-unit | v | 16 | supported | unit-stride load (extraction primitive: verify early) |
| `vse16.v` | RVV | rvv-mem-unit | VS-unit | v | 16 | supported | unit-stride store (extraction primitive: verify early) |
| `vle32.v` | RVV | rvv-mem-unit | VL-unit | v | 32 | supported | unit-stride load (extraction primitive: verify early) |
| `vse32.v` | RVV | rvv-mem-unit | VS-unit | v | 32 | supported | unit-stride store (extraction primitive: verify early) |
| `vle64.v` | RVV | rvv-mem-unit | VL-unit | v | 64 | supported | unit-stride load (extraction primitive: verify early) |
| `vse64.v` | RVV | rvv-mem-unit | VS-unit | v | 64 | supported | unit-stride store (extraction primitive: verify early) |
| `vlm.v` | RVV | rvv-mem-unit | VL-mask | v | 8 | supported | mask load EEW=1 (ceil(vl/8) bytes) |
| `vsm.v` | RVV | rvv-mem-unit | VS-mask | v | 8 | supported | mask store EEW=1 |
| `vle8ff.v` | RVV | rvv-mem-unit | VL-ff | v | 8 | blocked_illegal | fault-only-first load: dispatcher raises illegal (TODO not implemented) |
| `vle16ff.v` | RVV | rvv-mem-unit | VL-ff | v | 16 | blocked_illegal | fault-only-first load: dispatcher raises illegal (TODO not implemented) |
| `vle32ff.v` | RVV | rvv-mem-unit | VL-ff | v | 32 | blocked_illegal | fault-only-first load: dispatcher raises illegal (TODO not implemented) |
| `vle64ff.v` | RVV | rvv-mem-unit | VL-ff | v | 64 | blocked_illegal | fault-only-first load: dispatcher raises illegal (TODO not implemented) |
| `vlse8.v` | RVV | rvv-mem-strided | VL-strided | v | 8 | supported | strided load |
| `vsse8.v` | RVV | rvv-mem-strided | VS-strided | v | 8 | supported | strided store |
| `vlse16.v` | RVV | rvv-mem-strided | VL-strided | v | 16 | supported | strided load |
| `vsse16.v` | RVV | rvv-mem-strided | VS-strided | v | 16 | supported | strided store |
| `vlse32.v` | RVV | rvv-mem-strided | VL-strided | v | 32 | supported | strided load |
| `vsse32.v` | RVV | rvv-mem-strided | VS-strided | v | 32 | supported | strided store |
| `vlse64.v` | RVV | rvv-mem-strided | VL-strided | v | 64 | supported | strided load |
| `vsse64.v` | RVV | rvv-mem-strided | VS-strided | v | 64 | supported | strided store |
| `vluxei8.v` | RVV | rvv-mem-indexed | VL-idx-uo | v | 8 | supported | indexed-unordered (gather) load |
| `vloxei8.v` | RVV | rvv-mem-indexed | VL-idx-o | v | 8 | supported | indexed-ordered (gather) load |
| `vsuxei8.v` | RVV | rvv-mem-indexed | VS-idx-uo | v | 8 | supported | indexed-unordered (scatter) store |
| `vsoxei8.v` | RVV | rvv-mem-indexed | VS-idx-o | v | 8 | supported | indexed-ordered (scatter) store |
| `vluxei16.v` | RVV | rvv-mem-indexed | VL-idx-uo | v | 16 | supported | indexed-unordered (gather) load |
| `vloxei16.v` | RVV | rvv-mem-indexed | VL-idx-o | v | 16 | supported | indexed-ordered (gather) load |
| `vsuxei16.v` | RVV | rvv-mem-indexed | VS-idx-uo | v | 16 | supported | indexed-unordered (scatter) store |
| `vsoxei16.v` | RVV | rvv-mem-indexed | VS-idx-o | v | 16 | supported | indexed-ordered (scatter) store |
| `vluxei32.v` | RVV | rvv-mem-indexed | VL-idx-uo | v | 32 | supported | indexed-unordered (gather) load |
| `vloxei32.v` | RVV | rvv-mem-indexed | VL-idx-o | v | 32 | supported | indexed-ordered (gather) load |
| `vsuxei32.v` | RVV | rvv-mem-indexed | VS-idx-uo | v | 32 | supported | indexed-unordered (scatter) store |
| `vsoxei32.v` | RVV | rvv-mem-indexed | VS-idx-o | v | 32 | supported | indexed-ordered (scatter) store |
| `vluxei64.v` | RVV | rvv-mem-indexed | VL-idx-uo | v | 64 | supported | indexed-unordered (gather) load |
| `vloxei64.v` | RVV | rvv-mem-indexed | VL-idx-o | v | 64 | supported | indexed-ordered (gather) load |
| `vsuxei64.v` | RVV | rvv-mem-indexed | VS-idx-uo | v | 64 | supported | indexed-unordered (scatter) store |
| `vsoxei64.v` | RVV | rvv-mem-indexed | VS-idx-o | v | 64 | supported | indexed-ordered (scatter) store |
| `vl1re8.v` | RVV | rvv-mem-whole | VL-whole | v | 8 | supported | whole-register load, 1 reg(s) |
| `vl1re64.v` | RVV | rvv-mem-whole | VL-whole | v | 64 | supported | whole-register load EEW64, 1 reg(s) |
| `vs1r.v` | RVV | rvv-mem-whole | VS-whole | v | 8 | supported | whole-register store, 1 reg(s) |
| `vl2re8.v` | RVV | rvv-mem-whole | VL-whole | v | 8 | supported | whole-register load, 2 reg(s) |
| `vl2re64.v` | RVV | rvv-mem-whole | VL-whole | v | 64 | supported | whole-register load EEW64, 2 reg(s) |
| `vs2r.v` | RVV | rvv-mem-whole | VS-whole | v | 8 | supported | whole-register store, 2 reg(s) |
| `vl4re8.v` | RVV | rvv-mem-whole | VL-whole | v | 8 | supported | whole-register load, 4 reg(s) |
| `vl4re64.v` | RVV | rvv-mem-whole | VL-whole | v | 64 | supported | whole-register load EEW64, 4 reg(s) |
| `vs4r.v` | RVV | rvv-mem-whole | VS-whole | v | 8 | supported | whole-register store, 4 reg(s) |
| `vl8re8.v` | RVV | rvv-mem-whole | VL-whole | v | 8 | supported | whole-register load, 8 reg(s) |
| `vl8re64.v` | RVV | rvv-mem-whole | VL-whole | v | 64 | supported | whole-register load EEW64, 8 reg(s) |
| `vs8r.v` | RVV | rvv-mem-whole | VS-whole | v | 8 | supported | whole-register store, 8 reg(s) |
| `vlseg2e32.v` | RVV | rvv-mem-segment | VL-seg | v | 32 | blocked_silent | unit-stride segment load: nf not decoded -> silently treated as non-segment |
| `vsseg2e32.v` | RVV | rvv-mem-segment | VS-seg | v | 32 | blocked_silent | unit-stride segment store: silent mis-decode |
| `vlsseg2e32.v` | RVV | rvv-mem-segment | VL-seg-strd | v | 32 | blocked_silent | strided segment load: silent mis-decode |
| `vssseg2e32.v` | RVV | rvv-mem-segment | VS-seg-strd | v | 32 | blocked_silent | strided segment store: silent mis-decode |
| `vluxseg2ei32.v` | RVV | rvv-mem-segment | VL-seg-idx-uo | v | 32 | blocked_silent | indexed-unordered segment load: silent mis-decode |
| `vloxseg2ei32.v` | RVV | rvv-mem-segment | VL-seg-idx-o | v | 32 | blocked_silent | indexed-ordered segment load: silent mis-decode |
| `vsuxseg2ei32.v` | RVV | rvv-mem-segment | VS-seg-idx-uo | v | 32 | blocked_silent | indexed-unordered segment store: silent mis-decode |
| `vsoxseg2ei32.v` | RVV | rvv-mem-segment | VS-seg-idx-o | v | 32 | blocked_silent | indexed-ordered segment store: silent mis-decode |
| `vlseg2e32ff.v` | RVV | rvv-mem-segment | VL-seg-ff | v | 32 | blocked_illegal | fault-only-first segment load: ff lumop traps illegal regardless of nf |
| `vlseg4e32.v` | RVV | rvv-mem-segment | VL-seg | v | 32 | blocked_silent | unit-stride segment load: nf not decoded -> silently treated as non-segment |
| `vsseg4e32.v` | RVV | rvv-mem-segment | VS-seg | v | 32 | blocked_silent | unit-stride segment store: silent mis-decode |
| `vlsseg4e32.v` | RVV | rvv-mem-segment | VL-seg-strd | v | 32 | blocked_silent | strided segment load: silent mis-decode |
| `vssseg4e32.v` | RVV | rvv-mem-segment | VS-seg-strd | v | 32 | blocked_silent | strided segment store: silent mis-decode |
| `vluxseg4ei32.v` | RVV | rvv-mem-segment | VL-seg-idx-uo | v | 32 | blocked_silent | indexed-unordered segment load: silent mis-decode |
| `vloxseg4ei32.v` | RVV | rvv-mem-segment | VL-seg-idx-o | v | 32 | blocked_silent | indexed-ordered segment load: silent mis-decode |
| `vsuxseg4ei32.v` | RVV | rvv-mem-segment | VS-seg-idx-uo | v | 32 | blocked_silent | indexed-unordered segment store: silent mis-decode |
| `vsoxseg4ei32.v` | RVV | rvv-mem-segment | VS-seg-idx-o | v | 32 | blocked_silent | indexed-ordered segment store: silent mis-decode |
| `vlseg4e32ff.v` | RVV | rvv-mem-segment | VL-seg-ff | v | 32 | blocked_illegal | fault-only-first segment load: ff lumop traps illegal regardless of nf |
| `vlseg8e32.v` | RVV | rvv-mem-segment | VL-seg | v | 32 | blocked_silent | unit-stride segment load: nf not decoded -> silently treated as non-segment |
| `vsseg8e32.v` | RVV | rvv-mem-segment | VS-seg | v | 32 | blocked_silent | unit-stride segment store: silent mis-decode |
| `vlsseg8e32.v` | RVV | rvv-mem-segment | VL-seg-strd | v | 32 | blocked_silent | strided segment load: silent mis-decode |
| `vssseg8e32.v` | RVV | rvv-mem-segment | VS-seg-strd | v | 32 | blocked_silent | strided segment store: silent mis-decode |
| `vluxseg8ei32.v` | RVV | rvv-mem-segment | VL-seg-idx-uo | v | 32 | blocked_silent | indexed-unordered segment load: silent mis-decode |
| `vloxseg8ei32.v` | RVV | rvv-mem-segment | VL-seg-idx-o | v | 32 | blocked_silent | indexed-ordered segment load: silent mis-decode |
| `vsuxseg8ei32.v` | RVV | rvv-mem-segment | VS-seg-idx-uo | v | 32 | blocked_silent | indexed-unordered segment store: silent mis-decode |
| `vsoxseg8ei32.v` | RVV | rvv-mem-segment | VS-seg-idx-o | v | 32 | blocked_silent | indexed-ordered segment store: silent mis-decode |
| `vlseg8e32ff.v` | RVV | rvv-mem-segment | VL-seg-ff | v | 32 | blocked_illegal | fault-only-first segment load: ff lumop traps illegal regardless of nf |
| `vadd` | RVV | rvv-int-arith | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported |  |
| `vsub` | RVV | rvv-int-arith | OPIVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vrsub` | RVV | rvv-int-arith | OPIVX/VI | vx vi | 8,16,32,64 | supported | reverse subtract |
| `vand` | RVV | rvv-int-logical | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported |  |
| `vor` | RVV | rvv-int-logical | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported |  |
| `vxor` | RVV | rvv-int-logical | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported |  |
| `vsll` | RVV | rvv-int-shift | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported |  |
| `vsrl` | RVV | rvv-int-shift | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported |  |
| `vsra` | RVV | rvv-int-shift | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported |  |
| `vnsrl` | RVV | rvv-int-narrow | OPIVV/VX/VI | wv wx wi | 16,32,64 | supported | narrowing logical shift right |
| `vnsra` | RVV | rvv-int-narrow | OPIVV/VX/VI | wv wx wi | 16,32,64 | supported | narrowing arithmetic shift right |
| `vminu` | RVV | rvv-int-minmax | OPIVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vmin` | RVV | rvv-int-minmax | OPIVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vmaxu` | RVV | rvv-int-minmax | OPIVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vmax` | RVV | rvv-int-minmax | OPIVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vmseq` | RVV | rvv-int-cmp | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported |  |
| `vmsne` | RVV | rvv-int-cmp | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported |  |
| `vmsltu` | RVV | rvv-int-cmp | OPIVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vmslt` | RVV | rvv-int-cmp | OPIVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vmsleu` | RVV | rvv-int-cmp | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported |  |
| `vmsle` | RVV | rvv-int-cmp | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported |  |
| `vmsgtu` | RVV | rvv-int-cmp | OPIVX/VI | vx vi | 8,16,32,64 | supported |  |
| `vmsgt` | RVV | rvv-int-cmp | OPIVX/VI | vx vi | 8,16,32,64 | supported |  |
| `vmerge` | RVV | rvv-int-merge | OPIVV/VX/VI | vvm vxm vim | 8,16,32,64 | supported | mask-driven merge |
| `vmv.v` | RVV | rvv-int-merge | OPIVV/VX/VI | v x i | 8,16,32,64 | supported | vmv.v.v/.v.x/.v.i splat/copy |
| `vadc` | RVV | rvv-int-carry | OPIVV/VX/VI | vvm vxm vim | 8,16,32,64 | supported | add-with-carry |
| `vsbc` | RVV | rvv-int-carry | OPIVV/VX | vvm vxm | 8,16,32,64 | supported | subtract-with-borrow |
| `vmadc` | RVV | rvv-int-carry | OPIVV/VX/VI | vvm vxm vim vv vx vi | 8,16,32,64 | supported | produce carry-out mask |
| `vmsbc` | RVV | rvv-int-carry | OPIVV/VX | vvm vxm vv vx | 8,16,32,64 | supported | produce borrow-out mask |
| `vzext` | RVV | rvv-int-ext | OPMVV-VXUNARY0 | vf2 vf4 vf8 | 16,32,64 | supported | zero-extend vf2/vf4/vf8 |
| `vsext` | RVV | rvv-int-ext | OPMVV-VXUNARY0 | vf2 vf4 vf8 | 16,32,64 | supported | sign-extend vf2/vf4/vf8 |
| `vmul` | RVV | rvv-int-mul | OPMVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vmulh` | RVV | rvv-int-mul | OPMVV/VX | vv vx | 8,16,32,64 | supported | high bits, signed |
| `vmulhu` | RVV | rvv-int-mul | OPMVV/VX | vv vx | 8,16,32,64 | supported | high bits, unsigned |
| `vmulhsu` | RVV | rvv-int-mul | OPMVV/VX | vv vx | 8,16,32,64 | supported | high bits, signed*unsigned |
| `vdivu` | RVV | rvv-int-div | OPMVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vdiv` | RVV | rvv-int-div | OPMVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vremu` | RVV | rvv-int-div | OPMVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vrem` | RVV | rvv-int-div | OPMVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vmacc` | RVV | rvv-int-muladd | OPMVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vnmsac` | RVV | rvv-int-muladd | OPMVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vmadd` | RVV | rvv-int-muladd | OPMVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vnmsub` | RVV | rvv-int-muladd | OPMVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vwmul` | RVV | rvv-int-widen | OPMVV/VX | vv vx | 8,16,32 | supported |  |
| `vwmulu` | RVV | rvv-int-widen | OPMVV/VX | vv vx | 8,16,32 | supported |  |
| `vwmulsu` | RVV | rvv-int-widen | OPMVV/VX | vv vx | 8,16,32 | supported |  |
| `vwmacc` | RVV | rvv-int-widen | OPMVV/VX | vv vx | 8,16,32 | supported |  |
| `vwmaccu` | RVV | rvv-int-widen | OPMVV/VX | vv vx | 8,16,32 | supported |  |
| `vwmaccsu` | RVV | rvv-int-widen | OPMVV/VX | vv vx | 8,16,32 | supported |  |
| `vwmaccus` | RVV | rvv-int-widen | OPMVX | vx | 8,16,32 | supported |  |
| `vwaddu` | RVV | rvv-int-widen | OPMVV/VX | vv vx wv wx | 8,16,32 | supported |  |
| `vwadd` | RVV | rvv-int-widen | OPMVV/VX | vv vx wv wx | 8,16,32 | supported |  |
| `vwsubu` | RVV | rvv-int-widen | OPMVV/VX | vv vx wv wx | 8,16,32 | supported |  |
| `vwsub` | RVV | rvv-int-widen | OPMVV/VX | vv vx wv wx | 8,16,32 | supported |  |
| `vsaddu` | RVV | rvv-fixed | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported | saturating add unsigned |
| `vsadd` | RVV | rvv-fixed | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported | saturating add signed |
| `vssubu` | RVV | rvv-fixed | OPIVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vssub` | RVV | rvv-fixed | OPIVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vaaddu` | RVV | rvv-fixed | OPMVV/VX | vv vx | 8,16,32,64 | supported | averaging add unsigned (rounding via vxrm) |
| `vaadd` | RVV | rvv-fixed | OPMVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vasubu` | RVV | rvv-fixed | OPMVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vasub` | RVV | rvv-fixed | OPMVV/VX | vv vx | 8,16,32,64 | supported |  |
| `vsmul` | RVV | rvv-fixed | OPIVV/VX | vv vx | 8,16,32,64 | supported | fractional mul with rounding+saturate |
| `vssrl` | RVV | rvv-fixed | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported | scaling shift right logical (rounding) |
| `vssra` | RVV | rvv-fixed | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | supported | scaling shift right arithmetic |
| `vnclipu` | RVV | rvv-fixed | OPIVV/VX/VI | wv wx wi | 16,32,64 | supported | narrowing clip unsigned |
| `vnclip` | RVV | rvv-fixed | OPIVV/VX/VI | wv wx wi | 16,32,64 | supported | narrowing clip signed |
| `vfadd` | RVV | rvv-fp-arith | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfsub` | RVV | rvv-fp-arith | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfrsub` | RVV | rvv-fp-arith | OPFVF | vf | 16,32,64 | supported |  |
| `vfmul` | RVV | rvv-fp-arith | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfdiv` | RVV | rvv-fp-arith | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfrdiv` | RVV | rvv-fp-arith | OPFVF | vf | 16,32,64 | supported |  |
| `vfmacc` | RVV | rvv-fp-muladd | OPFVV/VF | vv vf | 16,32,64 | supported | FMA: oracle must be Spike (fusion) |
| `vfnmacc` | RVV | rvv-fp-muladd | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfmsac` | RVV | rvv-fp-muladd | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfnmsac` | RVV | rvv-fp-muladd | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfmadd` | RVV | rvv-fp-muladd | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfnmadd` | RVV | rvv-fp-muladd | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfmsub` | RVV | rvv-fp-muladd | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfnmsub` | RVV | rvv-fp-muladd | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfsqrt` | RVV | rvv-fp-unary | OPFVV-VFUNARY1 | v | 16,32,64 | supported |  |
| `vfrsqrt7` | RVV | rvv-fp-unary | OPFVV-VFUNARY1 | v | 16,32,64 | supported | 7-bit approx; oracle MUST be Spike |
| `vfrec7` | RVV | rvv-fp-unary | OPFVV-VFUNARY1 | v | 16,32,64 | supported | 7-bit approx; oracle MUST be Spike |
| `vfmin` | RVV | rvv-fp-minmax | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfmax` | RVV | rvv-fp-minmax | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfsgnj` | RVV | rvv-fp-sgnj | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfsgnjn` | RVV | rvv-fp-sgnj | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfsgnjx` | RVV | rvv-fp-sgnj | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vfclass` | RVV | rvv-fp-unary | OPFVV-VFUNARY1 | v | 16,32,64 | supported |  |
| `vmfeq` | RVV | rvv-fp-cmp | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vmfne` | RVV | rvv-fp-cmp | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vmflt` | RVV | rvv-fp-cmp | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vmfle` | RVV | rvv-fp-cmp | OPFVV/VF | vv vf | 16,32,64 | supported |  |
| `vmfgt` | RVV | rvv-fp-cmp | OPFVF | vf | 16,32,64 | supported |  |
| `vmfge` | RVV | rvv-fp-cmp | OPFVF | vf | 16,32,64 | supported |  |
| `vfmerge` | RVV | rvv-fp-merge | OPFVF | vfm | 16,32,64 | supported |  |
| `vfmv.v.f` | RVV | rvv-fp-merge | OPFVF | f | 16,32,64 | supported | FP splat |
| `vfcvt` | RVV | rvv-fp-cvt | OPFVV-VFUNARY0 | xu.f.v x.f.v rtz.xu.f.v rtz.x.f.v f.xu.v f.x.v | 16,32,64 | supported | same-width int<->fp convert |
| `vfwcvt` | RVV | rvv-fp-cvt | OPFVV-VFUNARY0 | xu.f.v x.f.v rtz.xu.f.v rtz.x.f.v f.xu.v f.x.v f.f.v | 16,32 | supported | widening convert |
| `vfncvt` | RVV | rvv-fp-cvt | OPFVV-VFUNARY0 | xu.f.w x.f.w rtz.xu.f.w rtz.x.f.w f.xu.w f.x.w f.f.w rod.f.f.w | 32,64 | supported | narrowing convert (incl round-to-odd) |
| `vfwadd` | RVV | rvv-fp-widen | OPFVV/VF | vv vf wv wf | 16,32 | supported |  |
| `vfwsub` | RVV | rvv-fp-widen | OPFVV/VF | vv vf wv wf | 16,32 | supported |  |
| `vfwmul` | RVV | rvv-fp-widen | OPFVV/VF | vv vf | 16,32 | supported |  |
| `vfwmacc` | RVV | rvv-fp-widen | OPFVV/VF | vv vf | 16,32 | supported |  |
| `vfwnmacc` | RVV | rvv-fp-widen | OPFVV/VF | vv vf | 16,32 | supported |  |
| `vfwmsac` | RVV | rvv-fp-widen | OPFVV/VF | vv vf | 16,32 | supported |  |
| `vfwnmsac` | RVV | rvv-fp-widen | OPFVV/VF | vv vf | 16,32 | supported |  |
| `vfmv.f.s` | RVV | rvv-fp-scalar | OPFVV-VWFUNARY0 | s | 16,32,64 | supported | extract element0 -> f reg |
| `vfmv.s.f` | RVV | rvv-fp-scalar | OPFVF-VRFUNARY0 | f | 16,32,64 | supported | f reg -> element0 |
| `vfslide1up` | RVV | rvv-perm | OPFVF | vf | 16,32,64 | supported |  |
| `vfslide1down` | RVV | rvv-perm | OPFVF | vf | 16,32,64 | supported |  |
| `vredsum` | RVV | rvv-red-int | OPMVV | vs | 8,16,32,64 | supported |  |
| `vredand` | RVV | rvv-red-int | OPMVV | vs | 8,16,32,64 | supported |  |
| `vredor` | RVV | rvv-red-int | OPMVV | vs | 8,16,32,64 | supported |  |
| `vredxor` | RVV | rvv-red-int | OPMVV | vs | 8,16,32,64 | supported |  |
| `vredminu` | RVV | rvv-red-int | OPMVV | vs | 8,16,32,64 | supported |  |
| `vredmin` | RVV | rvv-red-int | OPMVV | vs | 8,16,32,64 | supported |  |
| `vredmaxu` | RVV | rvv-red-int | OPMVV | vs | 8,16,32,64 | supported |  |
| `vredmax` | RVV | rvv-red-int | OPMVV | vs | 8,16,32,64 | supported |  |
| `vwredsumu` | RVV | rvv-red-int | OPIVV | vs | 8,16,32 | supported | widening sum reduction unsigned |
| `vwredsum` | RVV | rvv-red-int | OPIVV | vs | 8,16,32 | supported |  |
| `vfredosum` | RVV | rvv-red-fp | OPFVV | vs | 16,32,64 | supported | ordered FP sum (sequential) |
| `vfredusum` | RVV | rvv-red-fp | OPFVV | vs | 16,32,64 | supported | unordered FP sum: order impl-defined, pin inputs for diff |
| `vfredmin` | RVV | rvv-red-fp | OPFVV | vs | 16,32,64 | supported |  |
| `vfredmax` | RVV | rvv-red-fp | OPFVV | vs | 16,32,64 | supported |  |
| `vfwredosum` | RVV | rvv-red-fp | OPFVV | vs | 16,32 | supported | widening ordered FP sum |
| `vfwredusum` | RVV | rvv-red-fp | OPFVV | vs | 16,32 | supported | widening unordered: pin inputs for diff |
| `vmand` | RVV | rvv-mask-logical | OPMVV-MM | mm |  | supported |  |
| `vmnand` | RVV | rvv-mask-logical | OPMVV-MM | mm |  | supported |  |
| `vmandn` | RVV | rvv-mask-logical | OPMVV-MM | mm |  | supported | and-not (a & ~b) |
| `vmxor` | RVV | rvv-mask-logical | OPMVV-MM | mm |  | supported |  |
| `vmor` | RVV | rvv-mask-logical | OPMVV-MM | mm |  | supported |  |
| `vmnor` | RVV | rvv-mask-logical | OPMVV-MM | mm |  | supported |  |
| `vmorn` | RVV | rvv-mask-logical | OPMVV-MM | mm |  | supported | or-not (a | ~b) |
| `vmxnor` | RVV | rvv-mask-logical | OPMVV-MM | mm |  | supported |  |
| `vcpop.m` | RVV | rvv-mask-pop | OPMVV-VWXUNARY0 | m |  | supported | population count of mask |
| `vfirst.m` | RVV | rvv-mask-pop | OPMVV-VWXUNARY0 | m |  | supported | index of first set bit (-1 if none) |
| `vmsbf.m` | RVV | rvv-mask-set | OPMVV-VMUNARY0 | m |  | supported | set-before-first |
| `vmsif.m` | RVV | rvv-mask-set | OPMVV-VMUNARY0 | m |  | supported | set-including-first |
| `vmsof.m` | RVV | rvv-mask-set | OPMVV-VMUNARY0 | m |  | supported | set-only-first |
| `viota.m` | RVV | rvv-mask-iota | OPMVV-VMUNARY0 | m | 8,16,32,64 | supported | prefix sum of mask |
| `vid.v` | RVV | rvv-mask-iota | OPMVV-VMUNARY0 | v | 8,16,32,64 | supported | element index |
| `vmv.x.s` | RVV | rvv-mask-xmv | OPMVV-VWXUNARY0 | s | 8,16,32,64 | supported | element0 -> x reg |
| `vmv.s.x` | RVV | rvv-mask-xmv | OPMVX-VRXUNARY0 | x | 8,16,32,64 | supported | x reg -> element0 |
| `vslideup` | RVV | rvv-perm | OPIVX/VI | vx vi | 8,16,32,64 | supported |  |
| `vslidedown` | RVV | rvv-perm | OPIVX/VI | vx vi | 8,16,32,64 | supported |  |
| `vslide1up` | RVV | rvv-perm | OPMVX | vx | 8,16,32,64 | supported |  |
| `vslide1down` | RVV | rvv-perm | OPMVX | vx | 8,16,32,64 | supported |  |
| `vrgather` | RVV | rvv-perm | OPIVV/VX/VI | vv vx vi | 8,16,32,64 | blocked_illegal | not in op enum -> dispatcher illegal |
| `vrgatherei16` | RVV | rvv-perm | OPIVV | vv | 8,16,32,64 | blocked_illegal | not in op enum -> dispatcher illegal |
| `vcompress` | RVV | rvv-perm | OPMVV | vm | 8,16,32,64 | blocked_illegal | not in op enum -> dispatcher illegal |
| `vmv1r.v` | RVV | rvv-perm | OPIVI-whole | v |  | supported | whole-register move (decoded as VMERGE) |
| `vmv2r.v` | RVV | rvv-perm | OPIVI-whole | v |  | supported |  |
| `vmv4r.v` | RVV | rvv-perm | OPIVI-whole | v |  | supported |  |
| `vmv8r.v` | RVV | rvv-perm | OPIVI-whole | v |  | supported |  |
| `add` | RV64 | rv64i-reg | R | r |  | supported |  |
| `sub` | RV64 | rv64i-reg | R | r |  | supported |  |
| `sll` | RV64 | rv64i-reg | R | r |  | supported |  |
| `slt` | RV64 | rv64i-reg | R | r |  | supported |  |
| `sltu` | RV64 | rv64i-reg | R | r |  | supported |  |
| `xor` | RV64 | rv64i-reg | R | r |  | supported |  |
| `srl` | RV64 | rv64i-reg | R | r |  | supported |  |
| `sra` | RV64 | rv64i-reg | R | r |  | supported |  |
| `or` | RV64 | rv64i-reg | R | r |  | supported |  |
| `and` | RV64 | rv64i-reg | R | r |  | supported |  |
| `addi` | RV64 | rv64i-imm | I | i |  | supported |  |
| `slti` | RV64 | rv64i-imm | I | i |  | supported |  |
| `sltiu` | RV64 | rv64i-imm | I | i |  | supported |  |
| `xori` | RV64 | rv64i-imm | I | i |  | supported |  |
| `ori` | RV64 | rv64i-imm | I | i |  | supported |  |
| `andi` | RV64 | rv64i-imm | I | i |  | supported |  |
| `slli` | RV64 | rv64i-imm | I | i |  | supported |  |
| `srli` | RV64 | rv64i-imm | I | i |  | supported |  |
| `srai` | RV64 | rv64i-imm | I | i |  | supported |  |
| `lui` | RV64 | rv64i-imm | U | u |  | supported |  |
| `auipc` | RV64 | rv64i-imm | U | u |  | supported |  |
| `addw` | RV64 | rv64i-word | R | r |  | supported |  |
| `subw` | RV64 | rv64i-word | R | r |  | supported |  |
| `sllw` | RV64 | rv64i-word | R | r |  | supported |  |
| `srlw` | RV64 | rv64i-word | R | r |  | supported |  |
| `sraw` | RV64 | rv64i-word | R | r |  | supported |  |
| `addiw` | RV64 | rv64i-word | I | i |  | supported |  |
| `slliw` | RV64 | rv64i-word | I | i |  | supported |  |
| `srliw` | RV64 | rv64i-word | I | i |  | supported |  |
| `sraiw` | RV64 | rv64i-word | I | i |  | supported |  |
| `lb` | RV64 | rv64i-load | I | i |  | supported |  |
| `lh` | RV64 | rv64i-load | I | i |  | supported |  |
| `lw` | RV64 | rv64i-load | I | i |  | supported |  |
| `ld` | RV64 | rv64i-load | I | i |  | supported |  |
| `lbu` | RV64 | rv64i-load | I | i |  | supported |  |
| `lhu` | RV64 | rv64i-load | I | i |  | supported |  |
| `lwu` | RV64 | rv64i-load | I | i |  | supported |  |
| `sb` | RV64 | rv64i-store | S | s |  | supported |  |
| `sh` | RV64 | rv64i-store | S | s |  | supported |  |
| `sw` | RV64 | rv64i-store | S | s |  | supported |  |
| `sd` | RV64 | rv64i-store | S | s |  | supported |  |
| `beq` | RV64 | rv64i-branch | B | b |  | supported |  |
| `bne` | RV64 | rv64i-branch | B | b |  | supported |  |
| `blt` | RV64 | rv64i-branch | B | b |  | supported |  |
| `bge` | RV64 | rv64i-branch | B | b |  | supported |  |
| `bltu` | RV64 | rv64i-branch | B | b |  | supported |  |
| `bgeu` | RV64 | rv64i-branch | B | b |  | supported |  |
| `jal` | RV64 | rv64i-jump | J | j |  | supported |  |
| `jalr` | RV64 | rv64i-jump | I | i |  | supported |  |
| `fence` | RV64 | rv64i-sys | I | x |  | supported | Zifencei base fence |
| `fence.i` | RV64 | rv64i-sys | I | x |  | supported | Zifencei |
| `ecall` | RV64 | rv64i-sys | I | x |  | supported | traps; tested via deliberate trap path |
| `ebreak` | RV64 | rv64i-sys | I | x |  | supported | traps; tested via deliberate trap path |
| `mul` | RV64 | rv64m | R | r |  | supported |  |
| `mulh` | RV64 | rv64m | R | r |  | supported |  |
| `mulhsu` | RV64 | rv64m | R | r |  | supported |  |
| `mulhu` | RV64 | rv64m | R | r |  | supported |  |
| `div` | RV64 | rv64m | R | r |  | supported |  |
| `divu` | RV64 | rv64m | R | r |  | supported |  |
| `rem` | RV64 | rv64m | R | r |  | supported |  |
| `remu` | RV64 | rv64m | R | r |  | supported |  |
| `mulw` | RV64 | rv64m | R | r |  | supported |  |
| `divw` | RV64 | rv64m | R | r |  | supported |  |
| `divuw` | RV64 | rv64m | R | r |  | supported |  |
| `remw` | RV64 | rv64m | R | r |  | supported |  |
| `remuw` | RV64 | rv64m | R | r |  | supported |  |
| `lr.w` | RV64 | rv64a | R | r |  | supported |  |
| `sc.w` | RV64 | rv64a | R | r |  | supported |  |
| `lr.d` | RV64 | rv64a | R | r |  | supported |  |
| `sc.d` | RV64 | rv64a | R | r |  | supported |  |
| `amoswap.w` | RV64 | rv64a | R | r |  | supported |  |
| `amoswap.d` | RV64 | rv64a | R | r |  | supported |  |
| `amoadd.w` | RV64 | rv64a | R | r |  | supported |  |
| `amoadd.d` | RV64 | rv64a | R | r |  | supported |  |
| `amoxor.w` | RV64 | rv64a | R | r |  | supported |  |
| `amoxor.d` | RV64 | rv64a | R | r |  | supported |  |
| `amoand.w` | RV64 | rv64a | R | r |  | supported |  |
| `amoand.d` | RV64 | rv64a | R | r |  | supported |  |
| `amoor.w` | RV64 | rv64a | R | r |  | supported |  |
| `amoor.d` | RV64 | rv64a | R | r |  | supported |  |
| `amomin.w` | RV64 | rv64a | R | r |  | supported |  |
| `amomin.d` | RV64 | rv64a | R | r |  | supported |  |
| `amomax.w` | RV64 | rv64a | R | r |  | supported |  |
| `amomax.d` | RV64 | rv64a | R | r |  | supported |  |
| `amominu.w` | RV64 | rv64a | R | r |  | supported |  |
| `amominu.d` | RV64 | rv64a | R | r |  | supported |  |
| `amomaxu.w` | RV64 | rv64a | R | r |  | supported |  |
| `amomaxu.d` | RV64 | rv64a | R | r |  | supported |  |
| `flw` | RV64 | rv64f-mem | I | i |  | supported |  |
| `fsw` | RV64 | rv64f-mem | S | s |  | supported |  |
| `fadd.s` | RV64 | rv64f-arith | R | r |  | supported |  |
| `fsub.s` | RV64 | rv64f-arith | R | r |  | supported |  |
| `fmul.s` | RV64 | rv64f-arith | R | r |  | supported |  |
| `fdiv.s` | RV64 | rv64f-arith | R | r |  | supported |  |
| `fsqrt.s` | RV64 | rv64f-arith | R | r |  | supported |  |
| `fmadd.s` | RV64 | rv64f-fma | R4 | r4 |  | supported |  |
| `fmsub.s` | RV64 | rv64f-fma | R4 | r4 |  | supported |  |
| `fnmadd.s` | RV64 | rv64f-fma | R4 | r4 |  | supported |  |
| `fnmsub.s` | RV64 | rv64f-fma | R4 | r4 |  | supported |  |
| `fsgnj.s` | RV64 | rv64f-misc | R | r |  | supported |  |
| `fsgnjn.s` | RV64 | rv64f-misc | R | r |  | supported |  |
| `fsgnjx.s` | RV64 | rv64f-misc | R | r |  | supported |  |
| `fmin.s` | RV64 | rv64f-misc | R | r |  | supported |  |
| `fmax.s` | RV64 | rv64f-misc | R | r |  | supported |  |
| `fcvt.w.s` | RV64 | rv64f-cvt | R | r |  | supported |  |
| `fcvt.wu.s` | RV64 | rv64f-cvt | R | r |  | supported |  |
| `fcvt.s.w` | RV64 | rv64f-cvt | R | r |  | supported |  |
| `fcvt.s.wu` | RV64 | rv64f-cvt | R | r |  | supported |  |
| `fcvt.l.s` | RV64 | rv64f-cvt | R | r |  | supported |  |
| `fcvt.lu.s` | RV64 | rv64f-cvt | R | r |  | supported |  |
| `fcvt.s.l` | RV64 | rv64f-cvt | R | r |  | supported |  |
| `fcvt.s.lu` | RV64 | rv64f-cvt | R | r |  | supported |  |
| `fmv.x.w` | RV64 | rv64f-misc | R | r |  | supported |  |
| `fmv.w.x` | RV64 | rv64f-misc | R | r |  | supported |  |
| `feq.s` | RV64 | rv64f-misc | R | r |  | supported |  |
| `flt.s` | RV64 | rv64f-misc | R | r |  | supported |  |
| `fle.s` | RV64 | rv64f-misc | R | r |  | supported |  |
| `fclass.s` | RV64 | rv64f-misc | R | r |  | supported |  |
| `fld` | RV64 | rv64d-mem | I | i |  | supported |  |
| `fsd` | RV64 | rv64d-mem | S | s |  | supported |  |
| `fadd.d` | RV64 | rv64d-arith | R | r |  | supported |  |
| `fsub.d` | RV64 | rv64d-arith | R | r |  | supported |  |
| `fmul.d` | RV64 | rv64d-arith | R | r |  | supported |  |
| `fdiv.d` | RV64 | rv64d-arith | R | r |  | supported |  |
| `fsqrt.d` | RV64 | rv64d-arith | R | r |  | supported |  |
| `fmadd.d` | RV64 | rv64d-fma | R4 | r4 |  | supported |  |
| `fmsub.d` | RV64 | rv64d-fma | R4 | r4 |  | supported |  |
| `fnmadd.d` | RV64 | rv64d-fma | R4 | r4 |  | supported |  |
| `fnmsub.d` | RV64 | rv64d-fma | R4 | r4 |  | supported |  |
| `fsgnj.d` | RV64 | rv64d-misc | R | r |  | supported |  |
| `fsgnjn.d` | RV64 | rv64d-misc | R | r |  | supported |  |
| `fsgnjx.d` | RV64 | rv64d-misc | R | r |  | supported |  |
| `fmin.d` | RV64 | rv64d-misc | R | r |  | supported |  |
| `fmax.d` | RV64 | rv64d-misc | R | r |  | supported |  |
| `fcvt.s.d` | RV64 | rv64d-cvt | R | r |  | supported |  |
| `fcvt.d.s` | RV64 | rv64d-cvt | R | r |  | supported |  |
| `fcvt.w.d` | RV64 | rv64d-cvt | R | r |  | supported |  |
| `fcvt.wu.d` | RV64 | rv64d-cvt | R | r |  | supported |  |
| `fcvt.d.w` | RV64 | rv64d-cvt | R | r |  | supported |  |
| `fcvt.d.wu` | RV64 | rv64d-cvt | R | r |  | supported |  |
| `fcvt.l.d` | RV64 | rv64d-cvt | R | r |  | supported |  |
| `fcvt.lu.d` | RV64 | rv64d-cvt | R | r |  | supported |  |
| `fcvt.d.l` | RV64 | rv64d-cvt | R | r |  | supported |  |
| `fcvt.d.lu` | RV64 | rv64d-cvt | R | r |  | supported |  |
| `fmv.x.d` | RV64 | rv64d-misc | R | r |  | supported |  |
| `fmv.d.x` | RV64 | rv64d-misc | R | r |  | supported |  |
| `feq.d` | RV64 | rv64d-misc | R | r |  | supported |  |
| `flt.d` | RV64 | rv64d-misc | R | r |  | supported |  |
| `fle.d` | RV64 | rv64d-misc | R | r |  | supported |  |
| `fclass.d` | RV64 | rv64d-misc | R | r |  | supported |  |
| `csrrw` | RV64 | zicsr | I | i |  | supported | read/write CSR (e.g. vl, vtype, fcsr, cycle) |
| `csrrs` | RV64 | zicsr | I | i |  | supported | read/write CSR (e.g. vl, vtype, fcsr, cycle) |
| `csrrc` | RV64 | zicsr | I | i |  | supported | read/write CSR (e.g. vl, vtype, fcsr, cycle) |
| `csrrwi` | RV64 | zicsr | I | i |  | supported | read/write CSR (e.g. vl, vtype, fcsr, cycle) |
| `csrrsi` | RV64 | zicsr | I | i |  | supported | read/write CSR (e.g. vl, vtype, fcsr, cycle) |
| `csrrci` | RV64 | zicsr | I | i |  | supported | read/write CSR (e.g. vl, vtype, fcsr, cycle) |
| `c.*` | RV64 | rv64c | C | c |  | supported | compressed 16-bit forms; exercised implicitly by all compiled code |
| `Zba (sh1add/sh2add/sh3add/add.uw/...)` | RV64 | absent-ext | - |  |  | absent_ext | address-gen bitmanip: CVA6ConfigBExtEn=0 / not instantiated; would trap illegal |
| `Zbb (andn/orn/xnor/clz/ctz/cpop/min/max/rev8/...)` | RV64 | absent-ext | - |  |  | absent_ext | basic bitmanip: CVA6ConfigBExtEn=0 / not instantiated; would trap illegal |
| `Zbc (clmul/clmulh/clmulr)` | RV64 | absent-ext | - |  |  | absent_ext | carry-less multiply: CVA6ConfigBExtEn=0 / not instantiated; would trap illegal |
| `Zbs (bclr/bext/binv/bset)` | RV64 | absent-ext | - |  |  | absent_ext | single-bit bitmanip: CVA6ConfigBExtEn=0 / not instantiated; would trap illegal |
| `Zicond (czero.eqz/czero.nez)` | RV64 | absent-ext | - |  |  | absent_ext | conditional zero: CVA6ConfigBExtEn=0 / not instantiated; would trap illegal |
| `Zcb/Zcmp` | RV64 | absent-ext | - |  |  | absent_ext | extra compressed: CVA6ConfigBExtEn=0 / not instantiated; would trap illegal |
| `Zfh (scalar flh/fsh/fcvt.h.*)` | RV64 | absent-ext | - |  |  | absent_ext | scalar half precision: CVA6ConfigBExtEn=0 / not instantiated; would trap illegal |
