#include "interlock.h"
#include "internal.h"
#include "test_common.h"
#include <string.h>
int main(void) {
    uint8_t key[33] = {0};
    uint32_t before[28][4];
    interlock_key_ctx *ctx = NULL, *second = NULL;
    struct { interlock_key_ctx *slot; uint8_t rest[64]; } overlap = {NULL,{0}};
    CHECK(interlock_key_ctx_create(&ctx, key, 32) == INTERLOCK_OK);
    CHECK(ctx != NULL);
    memcpy(before, ctx->round_key, sizeof(before));
    memset(key, 0xff, sizeof(key));
    CHECK(memcmp(before, ctx->round_key, sizeof(before)) == 0);
    {
        interlock_key_ctx *saved = ctx;
        CHECK(interlock_key_ctx_create(&ctx, key, 32) == INTERLOCK_EINVAL);
        CHECK(ctx == saved);
    }
    CHECK(interlock_key_ctx_create(&second, key, 32) == INTERLOCK_OK);
    CHECK(second != ctx);
    CHECK(memcmp(second->round_key, before, sizeof(before)) != 0);
    interlock_key_ctx_free(second); second = NULL;
    CHECK(memcmp(ctx->round_key, before, sizeof(before)) == 0);
    interlock_key_ctx_free(ctx); ctx = NULL;
    interlock_key_ctx_free(NULL);
    CHECK(interlock_key_ctx_create(NULL, key, 32) == INTERLOCK_EINVAL);
    CHECK(interlock_key_ctx_create(&ctx, NULL, 32) == INTERLOCK_EINVAL && ctx == NULL);
    CHECK(interlock_key_ctx_create(&ctx, key, 31) == INTERLOCK_ELENGTH && ctx == NULL);
    CHECK(interlock_key_ctx_create(&ctx, key, 33) == INTERLOCK_ELENGTH && ctx == NULL);
    CHECK(interlock_key_ctx_create(&overlap.slot, (const uint8_t*)&overlap, 32) == INTERLOCK_EOVERLAP);
    CHECK(overlap.slot == NULL);
    for (int failure = 1; failure <= 10; ++failure) {
        if (failure > 5 && failure < 10) continue;
        il_test_failure = failure;
        CHECK(interlock_key_ctx_create(&ctx, key, 32) ==
              (failure <= 2 || failure == 10 ? INTERLOCK_ENOMEM : INTERLOCK_ECRYPTO));
        CHECK(ctx == NULL);
    }
    il_test_failure = 0;
    CHECK(interlock_key_ctx_create(&ctx, key, 32) == INTERLOCK_OK);
    interlock_key_ctx_free(ctx); ctx = NULL;
    return 0;
}
