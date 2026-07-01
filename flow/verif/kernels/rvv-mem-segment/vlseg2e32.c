/* Directed test: vlseg2e32.v (RVV unit-stride segment load, nf=2).
 * Memory layout [f0,f1,f0,f1,...]; deinterleaves field0->v8, field1->v9.
 * AraXL does not decode nf -> it mis-decodes this as a plain vle32 (silent, no
 * trap), so the DUT result differs from Spike's correct deinterleave. Expected
 * classification: FAIL_INCORRECT (a silent-correctness defect, not a hang/trap).
 */
#include "verif.h"

static int32_t IN[128] L2BUF;   /* interleaved [f0,f1,...] */
static int32_t R0[64]  L2BUF;   /* field0 result */
static int32_t R1[64]  L2BUF;   /* field1 result */

static void fill(void) {
    for (int i = 0; i < 64; i++) { IN[2 * i] = 1000 + i; IN[2 * i + 1] = 2000 + i; }
}

int main(void) {
    fill();
    VBEGIN();
    asm volatile("vsetvli t0,%3,e32,m1,ta,ma\n"
                 "vlseg2e32.v v8,(%0)\n"      /* v8=field0, v9=field1 */
                 "vse32.v v8,(%1)\n vse32.v v9,(%2)\n"
                 :: "r"(IN), "r"(R0), "r"(R1), "r"(16UL) : "t0", "memory");
    report_e32("vlseg2e32 field0 vl=16", R0, 16);
    report_e32("vlseg2e32 field1 vl=16", R1, 16);
    VEND();
    return 0;
}
