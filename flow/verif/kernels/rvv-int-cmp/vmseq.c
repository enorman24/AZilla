/* Directed test: vmseq (RVV integer set-equal compare -> mask) - OPIVV/VX/VI.
 * Result is a mask register; extracted with vsm.v as ceil(vl/8) bytes. vl chosen
 * as a multiple of 8 so no agnostic partial-byte bits enter the diff.
 */
#include "verif.h"

static int32_t A[64] L2BUF, B[64] L2BUF;
static uint8_t R[64] L2BUF;

static void fill(void) {
    for (int i = 0; i < 64; i++) {
        A[i] = i;
        B[i] = (i % 3 == 0) ? i : i + 100;   /* equal on every 3rd element */
    }
}

int main(void) {
    fill();
    VBEGIN();

    asm volatile("vsetvli t0,%3,e32,m1,ta,ma\n vle32.v v8,(%0)\n vle32.v v16,(%1)\n"
                 "vmseq.vv v24,v8,v16\n vsm.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(32UL) : "t0", "memory");
    report_bytes("vmseq.vv e32 m1 vl=32", R, 4);

    asm volatile("vsetvli t0,%3,e32,m1,ta,ma\n vle32.v v8,(%0)\n"
                 "vmseq.vx v24,v8,%4\n vsm.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(24UL), "r"(9L) : "t0", "memory");
    report_bytes("vmseq.vx e32 m1 vl=24 x=9", R, 3);

    asm volatile("vsetvli t0,%3,e32,m1,ta,ma\n vle32.v v8,(%0)\n"
                 "vmseq.vi v24,v8,5\n vsm.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(16UL) : "t0", "memory");
    report_bytes("vmseq.vi e32 m1 vl=16 imm=5", R, 2);

    VEND();
    return 0;
}
