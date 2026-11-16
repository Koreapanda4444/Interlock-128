#include "backend.h"
#include "interlock.h"
static int create(void **out, const uint8_t key[32], int decrypt) {
    interlock_key_ctx *ctx = NULL;
    (void)decrypt;
    if (interlock_key_ctx_create(&ctx, key, 32) != INTERLOCK_OK) return 0;
    *out = ctx;
    return 1;
}
static void destroy(void *ctx) { interlock_key_ctx_free(ctx); }
static int process(void *ctx, int decrypt, const uint8_t *in, uint8_t *out, size_t bytes) {
    for (size_t j = 0; j < bytes; j += 16) {
        interlock_status status = decrypt
            ? interlock_decrypt_block(ctx, in+j, 16, out+j, 16)
            : interlock_encrypt_block(ctx, in+j, 16, out+j, 16);
        if (status != INTERLOCK_OK) return 0;
    }
    return 1;
}
const bench_backend bench_interlock = {
    "Interlock-128", "one public API call per 16 bytes; full 28 rounds", create, destroy, process, NULL
};
