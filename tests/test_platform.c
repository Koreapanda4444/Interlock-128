#include <limits.h>
#include <stdint.h>
#include <stdio.h>
_Static_assert(CHAR_BIT == 8, "8-bit bytes required");
_Static_assert(sizeof(uint32_t) == 4, "32-bit word required");
_Static_assert(sizeof(uint64_t) == 8, "64-bit word required");
_Static_assert(UINT32_MAX == UINT32_C(0xffffffff), "unsigned word required");
int main(void) {
    printf("CHAR_BIT=%d uint32_t=%zu uintptr_t=%zu\n", CHAR_BIT, sizeof(uint32_t), sizeof(uintptr_t));
    return 0;
}
