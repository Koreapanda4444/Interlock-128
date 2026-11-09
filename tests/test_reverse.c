#include "internal.h"
#include "test_common.h"
#include "reference_parts.h"
#include <string.h>
static void independent_forward(uint32_t x[4], const uint32_t k[4]) {
    uint32_t a = x[0] ^ ref_fs(x[1], k[0]);
    uint32_t c = x[2] ^ ref_fm(x[3], k[1]);
    uint32_t b = x[1] ^ ref_fm(c, k[2]);
    uint32_t d = x[3] ^ ref_fs(a, k[3]);
    x[0] = ref_rol(c,5); x[1] = ref_rol(a,13);
    x[2] = ref_rol(d,21); x[3] = ref_rol(b,27);
}
static void independent_reverse(uint32_t x[4], const uint32_t k[4]) {
    uint32_t a = ref_rol(x[1],19), b = ref_rol(x[3],5);
    uint32_t c = ref_rol(x[0],27), d = ref_rol(x[2],11);
    d ^= ref_fs(a,k[3]); b ^= ref_fm(c,k[2]);
    c ^= ref_fm(d,k[1]); a ^= ref_fs(b,k[0]);
    x[0] = a; x[1] = b; x[2] = c; x[3] = d;
}
int main(void) {
    uint32_t random = UINT32_C(20261109);
    for (unsigned i = 0; i < 4096; ++i) {
        uint32_t original[4], key[4], forward[4], inverse[4], expected[4];
        for (unsigned j = 0; j < 4; ++j) {
            random = random * UINT32_C(1664525) + UINT32_C(1013904223);
            original[j] = i == 0 ? 0 : i == 1 ? UINT32_MAX : random;
            random = random * UINT32_C(1664525) + UINT32_C(1013904223);
            key[j] = i == 0 ? 0 : i == 1 ? UINT32_MAX : random;
        }
        memcpy(forward, original, sizeof(forward));
        memcpy(expected, original, sizeof(expected));
        il_test_forward_round(forward, key); independent_forward(expected, key);
        CHECK(memcmp(forward, expected, sizeof(forward)) == 0);
        il_test_reverse_round(forward, key);
        CHECK(memcmp(forward, original, sizeof(forward)) == 0);
        memcpy(inverse, original, sizeof(inverse));
        memcpy(expected, original, sizeof(expected));
        il_test_reverse_round(inverse, key); independent_reverse(expected, key);
        CHECK(memcmp(inverse, expected, sizeof(inverse)) == 0);
        il_test_forward_round(inverse, key);
        CHECK(memcmp(inverse, original, sizeof(inverse)) == 0);
    }
    return 0;
}
