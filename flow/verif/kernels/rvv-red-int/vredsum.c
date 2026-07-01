/* Directed test: vredsum.vs (RVV integer sum reduction).
 * vd[0] = vs1[0] + sum(vs2[0..vl-1]); result is the single element vd[0].
 * Extract by storing one element. Tail of vd is agnostic, so we report only [0,1).
 */
#include "verif.h"

static uint8_t A[1024] L2BUF;   /* operand byte pool (viewed per SEW) */
static uint8_t R[64]   L2BUF;   /* result */

static void fill(void) {
    for (int i = 0; i < 1024; i++) A[i] = (uint8_t)(i * 3u + 1u);
}

/* The reduction's scalar seed (vs1[0]) must be a SINGLE element: set it with
 * vmv.s.x (EMUL=1) so it never overlaps the LMUL-grouped vs2 nor reads OOB. */
int main(void) {
    fill();
    VBEGIN();

    asm volatile("vsetvli t0,%2,e8,m1,ta,ma\n vle8.v v8,(%0)\n"
                 "li t1,0x11\n vmv.s.x v4,t1\n"
                 "vredsum.vs v24,v8,v4\n vse8.v v24,(%1)\n"
                 :: "r"(A), "r"(R), "r"(50UL) : "t0", "t1", "memory");
    report_e8("vredsum.vs e8 m1 avl=50 seed=0x11", R, 1);

    asm volatile("vsetvli t0,%2,e32,m1,ta,ma\n vle32.v v8,(%0)\n"
                 "li t1,0x11\n vmv.s.x v4,t1\n"
                 "vredsum.vs v24,v8,v4\n vse32.v v24,(%1)\n"
                 :: "r"(A), "r"(R), "r"(33UL) : "t0", "t1", "memory");
    report_e32("vredsum.vs e32 m1 avl=33 seed=0x11", R, 1);

    asm volatile("vsetvli t0,%2,e32,m8,ta,ma\n vle32.v v8,(%0)\n"
                 "li t1,0x11\n vmv.s.x v4,t1\n"
                 "vredsum.vs v24,v8,v4\n vse32.v v24,(%1)\n"
                 :: "r"(A), "r"(R), "r"(200UL) : "t0", "t1", "memory");
    report_e32("vredsum.vs e32 m8 avl=200 seed=0x11", R, 1);

    asm volatile("vsetvli t0,%2,e64,m1,ta,ma\n vle64.v v8,(%0)\n"
                 "li t1,0x11\n vmv.s.x v4,t1\n"
                 "vredsum.vs v24,v8,v4\n vse64.v v24,(%1)\n"
                 :: "r"(A), "r"(R), "r"(17UL) : "t0", "t1", "memory");
    report_e64("vredsum.vs e64 m1 avl=17 seed=0x11", R, 1);

    VEND();
    return 0;
}
