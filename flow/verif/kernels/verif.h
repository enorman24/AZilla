/* verif.h - shared glue for AZilla RVV/RV64 directed verification kernels.
 *
 * A kernel prints its result region as raw hex words bracketed by markers; the
 * harness (verify_one.py) builds the SAME kernel for Spike (HTIF runtime) and
 * for the AraXL Verilator RTL (common runtime) and diffs the payloads. We dump
 * raw bit patterns (never %f) so FP results are compared bit-exactly.
 *
 * Buffers live in .l2 aligned to 128 bytes: AraXL deadlocks on non-64B-aligned
 * vector stores, so the result-extraction store (always unit-stride vse to one
 * of these buffers) is kept safely aligned; only the address an instruction
 * UNDER TEST computes (strided/indexed) is allowed to be the variable.
 */
#ifndef AZILLA_VERIF_H
#define AZILLA_VERIF_H

#include <stdint.h>
#ifndef SPIKE
#include "printf.h"
#endif
#include <stdio.h>

/* Reliable console for the AraXL/Verilator path.
 * apps/common/serial.c does a bare non-volatile `fake_uart = c`; consecutive
 * byte stores to the same MMIO address get coalesced/dropped by the CVA6 store
 * buffer, corrupting fast output (leading chars vanish). We force each byte to
 * commit as its own transaction with a fence before the next store. The Spike
 * build uses the HTIF console (syscalls.c), so this only applies to RTL builds
 * and we must NOT also link apps/common serial-llvm.c.o (would duplicate
 * _putchar). Guarded by SPIKE so the Spike build keeps its own printf path. */
#ifndef SPIKE
void _putchar(char character) {
    volatile char *u = (volatile char *)0xC0000000;
    *u = character;
    (void)*u;   /* readback forces the byte store to commit before the next */
}
#endif

#define VBEGIN()  printf("===VERIF-BEGIN===\n")
#define VEND()    printf("===VERIF-END===\n")
#define VLABEL(s) printf("#V %s\n", s)

#define L2BUF __attribute__((aligned(128), section(".l2")))

/* FNV-1a-64 over the result bytes: an EXACT bit-comparison digest (any single
 * differing byte changes it). Computed with scalar ops only (trusted base,
 * verified first) and identical on Spike and AraXL, so it is a sound
 * differential check. printf-over-serial is the sim bottleneck, so we print one
 * digest line per variant plus a few elementwise "peek" values for human audit;
 * the digest still covers ALL active elements. */
static inline uint64_t fnv64(const void *p, unsigned nbytes) {
    uint64_t h = 1469598103934665603ULL;
    const uint8_t *q = (const uint8_t *)p;
    for (unsigned i = 0; i < nbytes; i++) { h ^= q[i]; h *= 1099511628211ULL; }
    return h;
}
#define _PEEK(p, n, type, fmt)                                        \
    do {                                                              \
        int _pk = (n) < 4 ? (n) : 2;                                  \
        const type *_q = (const type *)(p);                           \
        for (int _i = 0; _i < _pk; _i++) printf(fmt "\n", (unsigned long)_q[_i]); \
        printf("DIG %016lx\n", (unsigned long)fnv64((p), (unsigned)(n) * sizeof(type))); \
    } while (0)

/* report n active elements of a result buffer (peek + exact digest) */
static inline void report_e8 (const char *l, const void *p, int n){ VLABEL(l); _PEEK(p,n,uint8_t,  "%02lx"); }
static inline void report_e16(const char *l, const void *p, int n){ VLABEL(l); _PEEK(p,n,uint16_t, "%04lx"); }
static inline void report_e32(const char *l, const void *p, int n){ VLABEL(l); _PEEK(p,n,uint32_t, "%08lx"); }
static inline void report_e64(const char *l, const void *p, int n){ VLABEL(l); _PEEK(p,n,uint64_t, "%016lx"); }
/* report raw bytes (mask registers stored via vsm.v): nbytes = ceil(vl/8) */
static inline void report_bytes(const char *l, const void *p, int nbytes){ VLABEL(l); _PEEK(p,nbytes,uint8_t,"%02lx"); }
/* report a single scalar xlen result (vcpop.m / vfirst.m / vmv.x.s) */
static inline void report_x(const char *l, uint64_t v){ VLABEL(l); printf("%016lx\nDIG %016lx\n",(unsigned long)v,(unsigned long)v); }

#endif /* AZILLA_VERIF_H */
