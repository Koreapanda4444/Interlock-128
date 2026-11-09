#include "internal.h"
#include "test_common.h"
#include "reference_parts.h"
int main(void) {
    uint32_t values[42] = {0,UINT32_MAX,1,UINT32_C(0xfffffffe),UINT32_C(0x7fffffff),
        UINT32_C(0x80000000),UINT32_C(0x0000ffff),UINT32_C(0x00010000),
        UINT32_C(0x55555555),UINT32_C(0xaaaaaaaa)};
    uint32_t random = UINT32_C(20261109);
    for (unsigned i = 0; i < 32; ++i) values[10+i] = UINT32_C(1) << i;
    for (size_t i = 0; i < 42; ++i) {
        CHECK(il_test_l32(values[i]) == ref_l(values[i]));
        for (size_t j = 0; j < 42; ++j) {
            CHECK(il_test_fs(values[i], values[j]) == ref_fs(values[i], values[j]));
            CHECK(il_test_fm(values[i], values[j]) == ref_fm(values[i], values[j]));
        }
    }
    for (unsigned i = 0; i < 1024; ++i) {
        uint32_t x, k;
        random = random * UINT32_C(1664525) + UINT32_C(1013904223); x = random;
        random = random * UINT32_C(1664525) + UINT32_C(1013904223); k = random;
        CHECK(il_test_fs(x, k) == ref_fs(x, k));
        CHECK(il_test_fm(x, k) == ref_fm(x, k));
    }
    return 0;
}
