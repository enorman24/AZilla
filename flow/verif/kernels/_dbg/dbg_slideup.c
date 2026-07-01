#include "verif.h"
static uint8_t A[256] L2BUF, R[256] L2BUF;
int main(void){ for(int i=0;i<256;i++)A[i]=i; VBEGIN();
  asm volatile("vsetvli t0,%2,e32,m1,ta,ma\n vle32.v v24,(%0)\n vle32.v v8,(%0)\n"
               "li t1,2\n vslideup.vx v24,v8,t1\n vse32.v v24,(%1)\n"
               ::"r"(A),"r"(R),"r"(16UL):"t0","t1","memory");
  report_e32("vslideup.vx e32 m1 avl=16 off=2", R, 16);
  VEND(); return 0; }
