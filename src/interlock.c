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
static uint32_t il_l32(uint32_t x) {
    return x ^ il_rol32(x, 3) ^ il_rol32(x, 17);
}
static uint32_t il_fs(uint32_t x, uint32_t k) {
    return il_l32(il_substitute(x ^ k));
}
static uint32_t il_fm(uint32_t x, uint32_t k) {
    uint32_t y = il_substitute(x ^ k);
    uint32_t u = (uint32_t)(y + il_rol32(k, 9));
    uint32_t v = il_rol32(y ^ k, 7);
    uint32_t w = il_rol32((uint32_t)(u + v), 11) ^ il_rol32(y & il_rol32(k, 3), 19);
    return il_l32(il_substitute(w ^ il_rol32(k, 13)));
}
#ifdef INTERLOCK_TESTING
uint32_t il_test_substitute(uint32_t x) { return il_substitute(x); }
uint32_t il_test_l32(uint32_t x) { return il_l32(x); }
uint32_t il_test_fs(uint32_t x, uint32_t k) { return il_fs(x, k); }
uint32_t il_test_fm(uint32_t x, uint32_t k) { return il_fm(x, k); }
#endif
