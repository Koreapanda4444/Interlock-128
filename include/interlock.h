#ifndef INTERLOCK_H
#define INTERLOCK_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define INTERLOCK_KEY_BYTES 32u
#define INTERLOCK_BLOCK_BYTES 16u
typedef struct interlock_key_ctx interlock_key_ctx;
typedef enum {
    INTERLOCK_OK = 0,
    INTERLOCK_EINVAL = 1,
    INTERLOCK_ELENGTH = 2,
    INTERLOCK_ECAPACITY = 3,
    INTERLOCK_EOVERLAP = 4,
    INTERLOCK_ENOMEM = 5,
    INTERLOCK_ECRYPTO = 6
} interlock_status;
/* *out_ctx must be initialized to NULL. Failure leaves the slot unchanged. */
interlock_status interlock_key_ctx_create(
    interlock_key_ctx **out_ctx, const uint8_t *key, size_t key_len);
/* NULL is allowed. Other pointers must identify a live owned context. */
void interlock_key_ctx_free(interlock_key_ctx *ctx);
/* Full 28 rounds. Exact in-place is supported; partial overlap is rejected. */
interlock_status interlock_encrypt_block(
    const interlock_key_ctx *ctx,
    const uint8_t *input, size_t input_len,
    uint8_t *output, size_t output_capacity);
interlock_status interlock_decrypt_block(
    const interlock_key_ctx *ctx,
    const uint8_t *input, size_t input_len,
    uint8_t *output, size_t output_capacity);
#ifdef __cplusplus
}
#endif
#endif
