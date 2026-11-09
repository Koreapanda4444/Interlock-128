#ifndef INTERLOCK_REFERENCE_PARTS_H
#define INTERLOCK_REFERENCE_PARTS_H
#include <stdint.h>
static uint32_t ref_rol(uint32_t x, unsigned n) {
    for (unsigned j = 0; j < n % 32; ++j) x = (uint32_t)((uint64_t)x * 2 + (x >> 31));
    return x;
}
static uint32_t ref_s(uint32_t x) {
    static const uint8_t s[] = {12,5,6,11,9,0,10,13,3,14,15,8,4,7,1,2};
    uint32_t out = 0;
    for (unsigned j = 0; j < 8; ++j) out += (uint32_t)s[(x >> (4*j)) & 15u] << (4*j);
    return out;
}
static uint32_t ref_l(uint32_t x) { return x ^ ref_rol(x, 3) ^ ref_rol(x, 17); }
static uint32_t ref_fs(uint32_t x, uint32_t k) { return ref_l(ref_s(x ^ k)); }
static uint32_t ref_fm(uint32_t x, uint32_t k) {
    uint32_t y = ref_s(x ^ k);
    uint64_t sum = (uint64_t)y + ref_rol(k, 9) + ref_rol(y ^ k, 7);
    uint32_t z = ref_rol((uint32_t)sum, 11) ^ ref_rol(y & ref_rol(k, 3), 19);
    return ref_l(ref_s(z ^ ref_rol(k, 13)));
}
#endif
