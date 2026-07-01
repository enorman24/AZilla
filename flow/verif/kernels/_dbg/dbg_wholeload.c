#include "verif.h"
static uint8_t A[2048] L2BUF, R[256] L2BUF;
int main(void){ for(int i=0;i<2048;i++)A[i]=(uint8_t)(i*7+3); VBEGIN();
  asm volatile("vl1re32.v v8,(%0)\n vsetivli t0,16,e32,m1,ta,ma\n vse32.v v8,(%1)\n"::"r"(A),"r"(R):"t0","memory");
  report_e32("vl1re32 first16", R, 16);
  VEND(); return 0; }
