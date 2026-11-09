#include "internal.h"
int il_expand_key(const uint8_t *key, size_t key_length, uint32_t round_key[28][4]) {
    static const uint8_t domain[] = "Interlock-128/roundkeys";
    uint8_t stream[448];
    il_span parts[2];
    int result;
    _Static_assert(sizeof(domain) == 24, "domain must contain exactly one NUL");
    if (key == NULL || key_length != 32 || round_key == NULL) return -1;
    parts[0].data = domain; parts[0].length = sizeof(domain);
    parts[1].data = key; parts[1].length = key_length;
    result = il_shake256(parts, 2, stream, sizeof(stream));
    if (result == 1) {
        for (size_t r = 0; r < 28; ++r) {
            for (size_t j = 0; j < 4; ++j) round_key[r][j] = il_load32(stream + 16*r + 4*j);
        }
    }
    il_cleanse(stream, sizeof(stream));
    return result;
}
