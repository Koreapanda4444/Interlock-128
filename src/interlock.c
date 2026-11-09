#include "internal.h"
#include <string.h>
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
static void il_forward_xors(uint32_t state[4], const uint32_t k[4]) {
    state[0] ^= il_fs(state[1], k[0]);
    state[2] ^= il_fm(state[3], k[1]);
    state[1] ^= il_fm(state[2], k[2]);
    state[3] ^= il_fs(state[0], k[3]);
}
static void il_forward_round(uint32_t state[4], const uint32_t k[4]) {
    uint32_t a, b, c, d;
    il_forward_xors(state, k);
    a = state[0]; b = state[1]; c = state[2]; d = state[3];
    state[0] = il_rol32(c, 5);
    state[1] = il_rol32(a, 13);
    state[2] = il_rol32(d, 21);
    state[3] = il_rol32(b, 27);
}
static inline void il_reverse_round(uint32_t state[4], const uint32_t k[4]) {
    uint32_t c = il_ror32(state[0], 5);
    uint32_t a = il_ror32(state[1], 13);
    uint32_t d = il_ror32(state[2], 21);
    uint32_t b = il_ror32(state[3], 27);
    d ^= il_fs(a, k[3]);
    b ^= il_fm(c, k[2]);
    c ^= il_fm(d, k[1]);
    a ^= il_fs(b, k[0]);
    state[0] = a; state[1] = b; state[2] = c; state[3] = d;
}
static interlock_status il_validate_block(
    const interlock_key_ctx *ctx, const uint8_t *input, size_t input_len,
    uint8_t *output, size_t output_capacity) {
    int overlap;
    if (ctx == NULL || input == NULL || output == NULL) return INTERLOCK_EINVAL;
    if (input_len != INTERLOCK_BLOCK_BYTES) return INTERLOCK_ELENGTH;
    if (output_capacity < INTERLOCK_BLOCK_BYTES) return INTERLOCK_ECAPACITY;
    overlap = il_ranges_overlap(input, INTERLOCK_BLOCK_BYTES, output, INTERLOCK_BLOCK_BYTES);
    if (overlap < 0) return INTERLOCK_EINVAL;
    if (input != output && overlap != 0) return INTERLOCK_EOVERLAP;
    return INTERLOCK_OK;
}
interlock_status interlock_encrypt_block(
    const interlock_key_ctx *ctx, const uint8_t *input, size_t input_len,
    uint8_t *output, size_t output_capacity) {
    uint32_t state[4];
    uint8_t block[INTERLOCK_BLOCK_BYTES];
    interlock_status status = il_validate_block(ctx, input, input_len, output, output_capacity);
    if (status != INTERLOCK_OK) return status;
    for (size_t j = 0; j < 4; ++j) state[j] = il_load32(input + 4*j);
    for (size_t r = 0; r < 28; ++r) il_forward_round(state, ctx->round_key[r]);
    for (size_t j = 0; j < 4; ++j) il_store32(block + 4*j, state[j]);
    memcpy(output, block, sizeof(block));
    il_cleanse(state, sizeof(state));
    il_cleanse(block, sizeof(block));
    return INTERLOCK_OK;
}
#ifdef INTERLOCK_TESTING
uint32_t il_test_substitute(uint32_t x) { return il_substitute(x); }
uint32_t il_test_l32(uint32_t x) { return il_l32(x); }
uint32_t il_test_fs(uint32_t x, uint32_t k) { return il_fs(x, k); }
uint32_t il_test_fm(uint32_t x, uint32_t k) { return il_fm(x, k); }
void il_test_forward_xors(uint32_t state[4], const uint32_t k[4]) { il_forward_xors(state, k); }
void il_test_forward_round(uint32_t state[4], const uint32_t k[4]) { il_forward_round(state, k); }
void il_test_reverse_round(uint32_t state[4], const uint32_t k[4]) { il_reverse_round(state, k); }
#endif
