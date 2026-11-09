#include "internal.h"
#include "test_common.h"
#include <string.h>
static void check_state(const uint32_t state[4], const char *hex) {
    for (size_t j = 0; j < 16; ++j) {
        unsigned expected;
        uint8_t actual = (uint8_t)(state[j/4] >> (8*(j%4)));
        CHECK(sscanf(hex+2*j, "%2x", &expected) == 1);
        CHECK(actual == expected);
    }
}
int main(void) {
    const uint8_t key[33] = {0};
    const uint32_t first[] = {UINT32_C(0x634a205d),UINT32_C(0xd56cc590),UINT32_C(0xd6cf518c),UINT32_C(0x9c8022bf)};
    const uint8_t domain[] = "Interlock-128/roundkeys";
    uint8_t wrong[448], correct[448], zero = 0;
    uint32_t schedule[28][4], state[4] = {0};
    il_span parts[3] = {{domain,sizeof(domain)},{key,32},{&zero,1}};
    CHECK(il_expand_key(key, 32, schedule) == 1);
    CHECK(memcmp(schedule[0], first, sizeof(first)) == 0);
    CHECK(il_shake256(parts, 2, correct, sizeof(correct)) == 1);
    for (size_t r = 0; r < 28; ++r) {
        for (size_t j = 0; j < 4; ++j) CHECK(schedule[r][j] == il_load32(correct+16*r+4*j));
        il_test_forward_round(state, schedule[r]);
        if (r == 0) check_state(state, "bc3f5fdced85606be7d9ad9f4bd37a1e");
        if (r == 3) check_state(state, "44045d030a10d4ccae45aa9b54964b1a");
    }
    check_state(state, "46272f4086f471ad8a7ec9c9917912bb");
    for (size_t r = 28; r-- > 0;) il_test_reverse_round(state, schedule[r]);
    check_state(state, "00000000000000000000000000000000");
    CHECK(il_shake256(parts, 3, wrong, sizeof(wrong)) == 1);
    CHECK(memcmp(correct, wrong, sizeof(correct)) != 0);
    parts[0].length = sizeof(domain)-1;
    CHECK(il_shake256(parts, 2, wrong, sizeof(wrong)) == 1);
    CHECK(memcmp(correct, wrong, sizeof(correct)) != 0);
    for (int failure = 1; failure <= 5; ++failure) {
        memset(schedule, 0xa5, sizeof(schedule));
        il_test_failure = failure;
        CHECK(il_expand_key(key, 32, schedule) == (failure <= 2 ? -2 : 0));
        for (size_t j = 0; j < sizeof(schedule); ++j) CHECK(((uint8_t*)schedule)[j] == 0xa5);
    }
    il_test_failure = 0;
    CHECK(il_expand_key(key, 31, schedule) == -1);
    CHECK(il_expand_key(key, 33, schedule) == -1);
    CHECK(il_expand_key(NULL, 32, schedule) == -1);
    CHECK(il_expand_key(key, 32, NULL) == -1);
    for (size_t j = 0; j < sizeof(schedule); ++j) CHECK(((uint8_t*)schedule)[j] == 0xa5);
    return 0;
}
