#include "internal.h"
#include "test_common.h"
#include "reference_parts.h"
#include <string.h>
int main(void) {
    const uint32_t k[4] = {UINT32_C(0x634a205d),UINT32_C(0xd56cc590),UINT32_C(0xd6cf518c),UINT32_C(0x9c8022bf)};
    const uint32_t before_permutation[4] = {UINT32_C(0x2f6b5b04),UINT32_C(0xcf5a6963),UINT32_C(0xe6e2f9fd),UINT32_C(0x6ecf3cfd)};
    const uint8_t expected[16] = {0xbc,0x3f,0x5f,0xdc,0xed,0x85,0x60,0x6b,0xe7,0xd9,0xad,0x9f,0x4b,0xd3,0x7a,0x1e};
    uint32_t state[4] = {0}, intermediate[4] = {0}, independent[4] = {0};
    uint8_t output[16];
    independent[0] ^= ref_fs(independent[1], k[0]);
    CHECK(independent[0] == before_permutation[0]);
    independent[2] ^= ref_fm(independent[3], k[1]);
    CHECK(independent[2] == before_permutation[2]);
    independent[1] ^= ref_fm(independent[2], k[2]);
    CHECK(independent[1] == before_permutation[1]);
    independent[3] ^= ref_fs(independent[0], k[3]);
    CHECK(independent[3] == before_permutation[3]);
    CHECK(ref_fm(0, k[2]) != before_permutation[1]);
    CHECK(ref_fs(0, k[3]) != before_permutation[3]);
    il_test_forward_xors(intermediate, k);
    CHECK(memcmp(intermediate, before_permutation, sizeof(intermediate)) == 0);
    il_test_forward_round(state, k);
    for (size_t j = 0; j < 4; ++j) il_store32(output + 4*j, state[j]);
    CHECK(memcmp(output, expected, 16) == 0);
    return 0;
}
