#include "internal.h"
#include "test_common.h"
static uint32_t table_reference(uint32_t x) {
    static const uint8_t s[16] = {12,5,6,11,9,0,10,13,3,14,15,8,4,7,1,2};
    uint32_t y = 0;
    for (unsigned j = 0; j < 8; ++j) y |= (uint32_t)s[(x >> (4*j)) & 15u] << (4*j);
    return y;
}
int main(void) {
    const uint32_t backgrounds[] = {0, UINT32_MAX, UINT32_C(0xa5a5a5a5), UINT32_C(0x12345678)};
    for (unsigned p = 0; p < 8; ++p) {
        for (uint32_t value = 0; value < 16; ++value) {
            for (size_t b = 0; b < sizeof(backgrounds)/sizeof(backgrounds[0]); ++b) {
                uint32_t x = (backgrounds[b] & ~(UINT32_C(15) << (4*p))) | (value << (4*p));
                CHECK(il_test_substitute(x) == table_reference(x));
            }
        }
    }
    return 0;
}
