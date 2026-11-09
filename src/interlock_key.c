#include "internal.h"
#include <stdlib.h>
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
interlock_status interlock_key_ctx_create(
    interlock_key_ctx **out_ctx, const uint8_t *key, size_t key_len) {
    interlock_key_ctx *ctx;
    int overlap, result;
    if (out_ctx == NULL || key == NULL) return INTERLOCK_EINVAL;
    if (key_len != INTERLOCK_KEY_BYTES) return INTERLOCK_ELENGTH;
    overlap = il_ranges_overlap(out_ctx, sizeof(*out_ctx), key, key_len);
    if (overlap < 0) return INTERLOCK_EINVAL;
    if (overlap != 0) return INTERLOCK_EOVERLAP;
    if (*out_ctx != NULL) return INTERLOCK_EINVAL;
    ctx = IL_FAIL(10) ? NULL : malloc(sizeof(*ctx));
    if (ctx == NULL) return INTERLOCK_ENOMEM;
    result = il_expand_key(key, key_len, ctx->round_key);
    if (result != 1) {
        il_cleanse(ctx, sizeof(*ctx));
        free(ctx);
        return result == -2 ? INTERLOCK_ENOMEM : result == 0 ? INTERLOCK_ECRYPTO : INTERLOCK_EINVAL;
    }
    *out_ctx = ctx;
    return INTERLOCK_OK;
}
void interlock_key_ctx_free(interlock_key_ctx *ctx) {
    if (ctx != NULL) {
        il_cleanse(ctx, sizeof(*ctx));
        free(ctx);
    }
}
