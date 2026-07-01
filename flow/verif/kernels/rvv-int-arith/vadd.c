/* Directed test: vadd (RVV integer add) - OPIVV/OPIVX/OPIVI.
 * Differential oracle: Spike vs AraXL. Reports only active elements [0,vl) so
 * tail-agnostic fill never affects the diff; masked/vl=0 variants use undisturbed
 * policy with a preloaded destination so masked-off/untouched lanes are
 * deterministic. See flow/verif/kernels/verif.h.
 */
#include "verif.h"

static uint8_t A[1024] L2BUF;    /* operand 1 byte pool (viewed at each SEW) */
static uint8_t B[1024] L2BUF;    /* operand 2 byte pool                      */
static uint8_t R[1024] L2BUF;    /* result extraction buffer                 */
static uint8_t D0[1024] L2BUF;   /* known preloaded-destination pattern      */
static uint8_t M[128]  L2BUF;    /* mask bits for v0                         */

static void fill(void) {
    for (int i = 0; i < 1024; i++) {
        A[i]  = (uint8_t)(i * 7u + 3u);
        B[i]  = (uint8_t)(i * 13u + 131u);
        D0[i] = (uint8_t)(0xC0u + i);
    }
    for (int i = 0; i < 128; i++) M[i] = (uint8_t)(0xA5u ^ (i * 3u));
}

int main(void) {
    fill();
    VBEGIN();

    /* ---- vv across SEW, LMUL=m1, tail AVLs ---- */
    asm volatile("vsetvli t0,%3,e8,m1,ta,ma\n vle8.v v8,(%0)\n vle8.v v16,(%1)\n"
                 "vadd.vv v24,v8,v16\n vse8.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(23UL) : "t0", "memory");
    report_e8("vadd.vv e8 m1 avl=23", R, 23);

    asm volatile("vsetvli t0,%3,e16,m1,ta,ma\n vle16.v v8,(%0)\n vle16.v v16,(%1)\n"
                 "vadd.vv v24,v8,v16\n vse16.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(20UL) : "t0", "memory");
    report_e16("vadd.vv e16 m1 avl=20", R, 20);

    asm volatile("vsetvli t0,%3,e32,m1,ta,ma\n vle32.v v8,(%0)\n vle32.v v16,(%1)\n"
                 "vadd.vv v24,v8,v16\n vse32.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(17UL) : "t0", "memory");
    report_e32("vadd.vv e32 m1 avl=17", R, 17);

    asm volatile("vsetvli t0,%3,e64,m1,ta,ma\n vle64.v v8,(%0)\n vle64.v v16,(%1)\n"
                 "vadd.vv v24,v8,v16\n vse64.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(9UL) : "t0", "memory");
    report_e64("vadd.vv e64 m1 avl=9", R, 9);

    /* ---- LMUL grouping at e32 ---- */
    asm volatile("vsetvli t0,%3,e32,m2,ta,ma\n vle32.v v8,(%0)\n vle32.v v16,(%1)\n"
                 "vadd.vv v24,v8,v16\n vse32.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(40UL) : "t0", "memory");
    report_e32("vadd.vv e32 m2 avl=40", R, 40);

    asm volatile("vsetvli t0,%3,e32,m8,ta,ma\n vle32.v v8,(%0)\n vle32.v v16,(%1)\n"
                 "vadd.vv v24,v8,v16\n vse32.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(100UL) : "t0", "memory");
    report_e32("vadd.vv e32 m8 avl=100", R, 100);

    asm volatile("vsetvli t0,%3,e32,mf2,ta,ma\n vle32.v v8,(%0)\n vle32.v v16,(%1)\n"
                 "vadd.vv v24,v8,v16\n vse32.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(10UL) : "t0", "memory");
    report_e32("vadd.vv e32 mf2 avl=10", R, 10);

    /* ---- vx / vi forms ---- */
    asm volatile("vsetvli t0,%3,e32,m1,ta,ma\n vle32.v v8,(%0)\n"
                 "vadd.vx v24,v8,%4\n vse32.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(17UL), "r"(0x12345L) : "t0", "memory");
    report_e32("vadd.vx e32 m1 avl=17 x=0x12345", R, 17);

    asm volatile("vsetvli t0,%3,e32,m1,ta,ma\n vle32.v v8,(%0)\n"
                 "vadd.vi v24,v8,-7\n vse32.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(17UL) : "t0", "memory");
    report_e32("vadd.vi e32 m1 avl=17 imm=-7", R, 17);

    /* ---- masked (mask-undisturbed): masked-off lanes keep preloaded D0 ---- */
    asm volatile("vsetvli t0,%4,e32,m1,ta,mu\n"
                 "vlm.v v0,(%5)\n"
                 "vle32.v v24,(%3)\n"
                 "vle32.v v8,(%0)\n vle32.v v16,(%1)\n"
                 "vadd.vv v24,v8,v16,v0.t\n"
                 "vse32.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(D0), "r"(16UL), "r"(M) : "t0", "memory");
    report_e32("vadd.vv e32 m1 masked(mu) avl=16", R, 16);

    /* ---- vl=0: op must modify nothing ---- */
    asm volatile("vsetivli t0,8,e32,m1,ta,ma\n vle32.v v24,(%3)\n"
                 "vsetvli t0,zero,e32,m1,tu,ma\n"
                 "vle32.v v8,(%0)\n vle32.v v16,(%1)\n"
                 "vadd.vv v24,v8,v16\n"
                 "vsetivli t0,8,e32,m1,ta,ma\n vse32.v v24,(%2)\n"
                 :: "r"(A), "r"(B), "r"(R), "r"(D0) : "t0", "memory");
    report_e32("vadd.vv e32 vl=0 (dest preserved)", R, 8);

    VEND();
    return 0;
}
