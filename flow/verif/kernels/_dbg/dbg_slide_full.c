#include "verif.h"
static uint32_t A[64] L2BUF, R[64] L2BUF;
int main(void){ for(int i=0;i<64;i++){A[i]=100+i; R[i]=0;} VBEGIN();
  /* preload dest with 0xDD; vslideup by 3 -> dest[0..2] keep 0xDD, dest[3..15]=A[0..12] */
  asm volatile("vsetvli t0,%2,e32,m1,ta,ma\n"
    "li t1,0xDD\n vmv.v.x v24,t1\n"      /* dest = 0xDD splat (vmv.v.x verified PASS) */
    "vle32.v v8,(%0)\n li t1,3\n vslideup.vx v24,v8,t1\n vse32.v v24,(%1)\n"
    ::"r"(A),"r"(R),"r"(16UL):"t0","t1","memory");
  printf("vslideup.vx by 3 (expect: DD DD DD 100 101 102...112):\n");
  for(int i=0;i<16;i++) printf("%d ",(int)R[i]); printf("\n");
  VEND(); return 0; }
