#include "internal.h"
/* PRESENT ANF evaluated on eight independent nibble lanes. */
static uint32_t il_substitute(uint32_t x) {
    const uint32_t lanes = UINT32_C(0x11111111);
    uint32_t x0 = x & lanes, x1 = (x >> 1) & lanes;
    uint32_t x2 = (x >> 2) & lanes, x3 = (x >> 3) & lanes;
    uint32_t y0 = x0 ^ x2 ^ (x1 & x2) ^ x3;
    uint32_t y1 = x1 ^ (x0 & x1 & x2) ^ x3 ^ (x1 & x3) ^
                  (x0 & x1 & x3) ^ (x2 & x3) ^ (x0 & x2 & x3);
    uint32_t y2 = lanes ^ (x0 & x1) ^ x2 ^ x3 ^ (x0 & x3) ^
                  (x1 & x3) ^ (x0 & x1 & x3) ^ (x0 & x2 & x3);
    uint32_t y3 = lanes ^ x0 ^ x1 ^ (x1 & x2) ^ (x0 & x1 & x2) ^
                  x3 ^ (x0 & x1 & x3) ^ (x0 & x2 & x3);
    return y0 | (y1 << 1) | (y2 << 2) | (y3 << 3);
}
#ifdef INTERLOCK_TESTING
uint32_t il_test_substitute(uint32_t x) { return il_substitute(x); }
#endif
