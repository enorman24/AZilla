/* Directed test: vrgather.vv (RVV gather) - OPIVV.
 * vd[i] = vs2[vs1[i]]. Spike executes it; AraXL does NOT decode vrgather (not in
 * the op enum) and raises an illegal-instruction trap (mcause=2). Expected
 * classification: BLOCKED (illegal / not implemented), distinct from FAIL.
 */
#include "verif.h"

static int32_t A[64]   L2BUF;   /* data */
static int32_t IDX[64] L2BUF;   /* gather indices */
static int32_t R[64]   L2BUF;

static void fill(void) {
    for (int i = 0; i < 64; i++) { A[i] = 100 + i; IDX[i] = 63 - i; }   /* reverse */
}

int main(void) {
    fill();
    VBEGIN();
    asm volatile("vsetvli t0,%3,e32,m1,ta,ma\n vle32.v v8,(%0)\n vle32.v v16,(%1)\n"
                 "vrgather.vv v24,v8,v16\n vse32.v v24,(%2)\n"
                 :: "r"(A), "r"(IDX), "r"(R), "r"(16UL) : "t0", "memory");
    report_e32("vrgather.vv e32 m1 vl=16", R, 16);
    VEND();
    return 0;
}
