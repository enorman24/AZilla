#include "verif.h"
static uint8_t R[256] L2BUF;
int main(void){ VBEGIN();
  asm volatile("vsetvli t0,%1,e32,m1,ta,ma\n vid.v v24\n vse32.v v24,(%0)\n"::"r"(R),"r"(40UL):"t0","memory");
  for(int i=0;i<40;i++) report_e32("vid.v[i]", R+i*4, 1);
  VEND(); return 0; }
