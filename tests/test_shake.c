#include "internal.h"
#include "test_common.h"
#include <string.h>
static void decode(const char *hex, uint8_t *out, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        unsigned x;
        CHECK(sscanf(hex + 2*i, "%2x", &x) == 1);
        out[i] = (uint8_t)x;
    }
}
int main(void) {
    uint8_t expected[64], empty[448], whole[448], split[448], guard[450];
    const uint8_t abc[] = {'a','b','c'};
    const il_span one[] = {{abc, 3}};
    const il_span parts[] = {{abc, 1}, {NULL, 0}, {abc + 1, 1}, {abc + 2, 1}};
    decode("46b9dd2b0ba88d13233b3feb743eeb243fcd52ea62b81b82b50c27646ed5762fd75dc4ddd8c0f200cb05019d67b592f6fc821c49479ab48640292eacb3b7c4be", expected, 64);
    CHECK(il_shake256(NULL, 0, empty, sizeof(empty)) == 1);
    CHECK(memcmp(empty, expected, 64) == 0);
    CHECK(il_shake256(one, 1, whole, sizeof(whole)) == 1);
    CHECK(il_shake256(parts, 4, split, sizeof(split)) == 1);
    CHECK(memcmp(whole, split, sizeof(whole)) == 0);
    for (int failure = 1; failure <= 5; ++failure) {
        memset(guard, 0xa5, sizeof(guard));
        il_test_failure = failure;
        CHECK(il_shake256(one, 1, guard + 1, 448) == (failure <= 2 ? -2 : 0));
        for (size_t j = 0; j < sizeof(guard); ++j) CHECK(guard[j] == 0xa5);
    }
    il_test_failure = 0;
    CHECK(il_shake256(NULL, 1, guard, 64) == -1);
    CHECK(il_shake256(one, 1, NULL, 64) == -1);
    CHECK(il_shake256(one, 1, guard, 0) == -1);
    { il_span invalid = {NULL, 1}; CHECK(il_shake256(&invalid, 1, guard, 64) == -1); }
    memset(guard, 0xa5, sizeof(guard));
    CHECK(il_shake256(one, 1, guard + 1, 448) == 1);
    CHECK(guard[0] == 0xa5 && guard[449] == 0xa5);
    CHECK(memcmp(guard + 1, whole, 448) == 0);
    il_cleanse(guard, sizeof(guard));
    for (size_t j = 0; j < sizeof(guard); ++j) CHECK(guard[j] == 0);
    return 0;
}
