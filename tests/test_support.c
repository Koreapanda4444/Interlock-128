#include "internal.h"
#include "test_common.h"
#include <string.h>
int main(void) {
    const uint32_t x = UINT32_C(0x81234567);
    uint8_t bytes[64];
    uintptr_t end = 123;
    memset(bytes, 0xa5, sizeof(bytes));
    CHECK(il_rol32(x, 0) == x && il_rol32(x, 32) == x);
    CHECK(il_ror32(x, 0) == x && il_ror32(x, 32) == x);
    CHECK(il_rol32(x, 1) == UINT32_C(0x02468acf));
    CHECK(il_rol32(x, 31) == UINT32_C(0xc091a2b3));
    for (unsigned i = 0; i <= 64; ++i) CHECK(il_ror32(il_rol32(x, i), i) == x);
    il_store32(bytes + 1, x);
    CHECK(bytes[0] == 0xa5 && bytes[5] == 0xa5);
    CHECK(bytes[1] == 0x67 && bytes[2] == 0x45 && bytes[3] == 0x23 && bytes[4] == 0x81);
    CHECK(il_load32(bytes + 1) == x);
    CHECK(il_range_end(UINTPTR_MAX - 16, 16, &end) && end == UINTPTR_MAX);
    CHECK(!il_range_end(UINTPTR_MAX - 15, 16, &end) && end == UINTPTR_MAX);
    CHECK(il_range_end(UINTPTR_MAX, 0, &end) && end == UINTPTR_MAX);
    CHECK(il_ranges_overlap(bytes, 16, bytes + 16, 16) == 0);
    CHECK(il_ranges_overlap(bytes, 16, bytes, 16) == 1);
    CHECK(il_ranges_overlap(bytes, 0, bytes, 16) == 0);
    for (size_t i = 1; i < 16; ++i) {
        CHECK(il_ranges_overlap(bytes, 16, bytes + i, 16) == 1);
        CHECK(il_ranges_overlap(bytes + i, 16, bytes, 16) == 1);
    }
    CHECK(il_ranges_overlap(bytes, 16, bytes + 32, 16) == 0);
    return 0;
}
