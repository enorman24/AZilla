/* Directed test: representative RV64 scalar ops (I/M/F/D + Zicsr).
 * Each op reported individually (label + value) so any Spike-vs-AraXL diff is
 * localized to a specific instruction. FP results reported as raw bits.
 */
#include "verif.h"

int main(void) {
    VBEGIN();
    volatile long a = 0x0123456789ABCDEFL, b = -0x55AA55AAL;
    long o;

    asm volatile("add  %0,%1,%2" : "=r"(o) : "r"(a), "r"(b)); report_x("add",  (uint64_t)o);
    asm volatile("sub  %0,%1,%2" : "=r"(o) : "r"(a), "r"(b)); report_x("sub",  (uint64_t)o);
    asm volatile("sll  %0,%1,%2" : "=r"(o) : "r"(a), "r"(7L)); report_x("sll",  (uint64_t)o);
    asm volatile("sra  %0,%1,%2" : "=r"(o) : "r"(a), "r"(7L)); report_x("sra",  (uint64_t)o);
    asm volatile("addw %0,%1,%2" : "=r"(o) : "r"(a), "r"(b)); report_x("addw", (uint64_t)o);
    asm volatile("sllw %0,%1,%2" : "=r"(o) : "r"(a), "r"(5L)); report_x("sllw", (uint64_t)o);
    asm volatile("mul    %0,%1,%2" : "=r"(o) : "r"(a), "r"(b)); report_x("mul",    (uint64_t)o);
    asm volatile("mulh   %0,%1,%2" : "=r"(o) : "r"(a), "r"(b)); report_x("mulh",   (uint64_t)o);
    asm volatile("mulhu  %0,%1,%2" : "=r"(o) : "r"(a), "r"(b)); report_x("mulhu",  (uint64_t)o);
    asm volatile("div    %0,%1,%2" : "=r"(o) : "r"(a), "r"(b)); report_x("div",    (uint64_t)o);
    asm volatile("rem    %0,%1,%2" : "=r"(o) : "r"(a), "r"(b)); report_x("rem",    (uint64_t)o);
    asm volatile("divuw  %0,%1,%2" : "=r"(o) : "r"(a), "r"(b)); report_x("divuw",  (uint64_t)o);

    float  fa = 3.5f, fb = -1.25f, fo; double da = 1e10 + 0.5, db = 7.0, do_;
    uint32_t fb32; uint64_t fb64;
    asm volatile("fadd.s %0,%1,%2" : "=f"(fo) : "f"(fa), "f"(fb)); fb32 = *(uint32_t *)&fo; report_x("fadd.s", fb32);
    asm volatile("fmul.s %0,%1,%2" : "=f"(fo) : "f"(fa), "f"(fb)); fb32 = *(uint32_t *)&fo; report_x("fmul.s", fb32);
    asm volatile("fsqrt.s %0,%1"   : "=f"(fo) : "f"(fa));          fb32 = *(uint32_t *)&fo; report_x("fsqrt.s", fb32);
    asm volatile("fadd.d %0,%1,%2" : "=f"(do_) : "f"(da), "f"(db)); fb64 = *(uint64_t *)&do_; report_x("fadd.d", fb64);
    asm volatile("fdiv.d %0,%1,%2" : "=f"(do_) : "f"(da), "f"(db)); fb64 = *(uint64_t *)&do_; report_x("fdiv.d", fb64);
    { long w; asm volatile("fcvt.w.s %0,%1" : "=r"(w) : "f"(fa)); report_x("fcvt.w.s(3.5)", (uint64_t)w); }
    { double dd; asm volatile("fcvt.d.s %0,%1" : "=f"(dd) : "f"(fa)); report_x("fcvt.d.s", *(uint64_t *)&dd); }

    /* csrr of vtype (config-independent: encodes SEW/LMUL, not VLEN). vlenb is
     * intentionally NOT tested cross-sim: AraXL VLEN=16384 vs Spike-oracle 4096. */
    { long vtype; asm volatile("vsetivli t0,7,e32,m2,ta,ma\n csrr %0,0xC21" : "=r"(vtype) :: "t0"); report_x("csrr vtype(e32,m2)", (uint64_t)vtype); }
    { long vl; asm volatile("vsetivli %0,7,e32,m2,ta,ma" : "=r"(vl)); report_x("vsetivli->vl(avl7,m2)", (uint64_t)vl); }

    VEND();
    return 0;
}
