#ifndef INTERLOCK_INTERNAL_H
#define INTERLOCK_INTERNAL_H
#include <stddef.h>
#include <stdint.h>
#include <limits.h>
_Static_assert(CHAR_BIT == 8 && sizeof(uint32_t) == 4, "unsupported integer platform");
#ifndef UINTPTR_MAX
#error Interlock requires uintptr_t and flat address representations
#endif
static inline uint32_t il_rol32(uint32_t x, unsigned n) {
    n &= 31u;
    return (x << n) | (x >> ((32u - n) & 31u));
}
static inline uint32_t il_ror32(uint32_t x, unsigned n) {
    n &= 31u;
    return (x >> n) | (x << ((32u - n) & 31u));
}
static inline uint32_t il_load32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static inline void il_store32(uint8_t *p, uint32_t x) {
    p[0] = (uint8_t)x; p[1] = (uint8_t)(x >> 8);
    p[2] = (uint8_t)(x >> 16); p[3] = (uint8_t)(x >> 24);
}
int il_range_end(uintptr_t start, size_t length, uintptr_t *end);
/* -1: integer overflow, 0: disjoint, 1: overlap. Valid objects remain required. */
int il_ranges_overlap(const void *a, size_t na, const void *b, size_t nb);
typedef struct { const uint8_t *data; size_t length; } il_span;
/* 1: success, 0: EVP failure, -1: invalid arguments, -2: allocation failure. */
int il_shake256(const il_span *parts, size_t count, uint8_t *output, size_t length);
void il_cleanse(void *p, size_t length);
int il_expand_key(const uint8_t *key, size_t key_length, uint32_t round_key[28][4]);
#ifdef INTERLOCK_TESTING
extern int il_test_failure;
uint32_t il_test_substitute(uint32_t x);
uint32_t il_test_l32(uint32_t x);
uint32_t il_test_fs(uint32_t x, uint32_t k);
uint32_t il_test_fm(uint32_t x, uint32_t k);
void il_test_forward_xors(uint32_t state[4], const uint32_t k[4]);
void il_test_forward_round(uint32_t state[4], const uint32_t k[4]);
void il_test_reverse_round(uint32_t state[4], const uint32_t k[4]);
#define IL_FAIL(point) (il_test_failure == (point))
#else
#define IL_FAIL(point) 0
#endif
#endif
