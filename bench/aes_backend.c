#include "backend.h"
#include <limits.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/provider.h>
static EVP_CIPHER *cipher = NULL;
static int create(void **out, const uint8_t key[32], int decrypt) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (ctx == NULL) return 0;
    if (EVP_CipherInit_ex2(ctx,cipher,key,NULL,decrypt ? 0 : 1,NULL) != 1 ||
        EVP_CIPHER_CTX_set_padding(ctx,0) != 1) {
        EVP_CIPHER_CTX_free(ctx);
        return 0;
    }
    *out = ctx;
    return 1;
}
static void destroy(void *ctx) { EVP_CIPHER_CTX_free(ctx); }
static int process_batch(void *ctx, int decrypt, const uint8_t *in, uint8_t *out, size_t bytes) {
    int written = 0;
    (void)decrypt;
    if (bytes > INT_MAX || bytes%16 != 0) return 0;
    return EVP_CipherUpdate(ctx,out,&written,in,(int)bytes) == 1 && written == (int)bytes;
}
static int process_blocks(void *ctx, int decrypt, const uint8_t *in, uint8_t *out, size_t bytes) {
    if (bytes%16 != 0) return 0;
    for (size_t j = 0; j < bytes; j += 16)
        if (!process_batch(ctx,decrypt,in+j,out+j,16)) return 0;
    return 1;
}
static int finish(void *ctx) {
    uint8_t out[16];
    int written = -1;
    return EVP_CipherFinal_ex(ctx,out,&written) == 1 && written == 0;
}
int bench_aes_init(void) {
    /* FIPS197 (2001), Appendix C.3; data/algorithm fetch excluded from timing. */
    static const uint8_t plain[16] = {0x00,0x11,0x22,0x33,0x44,0x55,0x66,0x77,
                                     0x88,0x99,0xaa,0xbb,0xcc,0xdd,0xee,0xff};
    static const uint8_t expected[16] = {0x8e,0xa2,0xb7,0xca,0x51,0x67,0x45,0xbf,
                                        0xea,0xfc,0x49,0x90,0x4b,0x49,0x60,0x89};
    uint8_t key[32], out[16];
    void *ctx = NULL;
    int ok;
    cipher = EVP_CIPHER_fetch(NULL,"AES-256-ECB",NULL);
    if (cipher == NULL) return 0;
    for (size_t j = 0; j < 32; ++j) key[j] = (uint8_t)j;
    for (int decrypt = 0; decrypt <= 1; ++decrypt) {
        if (!create(&ctx,key,decrypt)) return 0;
        ok = process_batch(ctx,decrypt,decrypt ? expected : plain,out,16) && finish(ctx) &&
             memcmp(out,decrypt ? plain : expected,16) == 0;
        destroy(ctx); ctx = NULL;
        if (!ok) return 0;
    }
    return 1;
}
const char *bench_aes_provider(void) {
    const OSSL_PROVIDER *provider = EVP_CIPHER_get0_provider(cipher);
    return provider == NULL ? "unknown" : OSSL_PROVIDER_get0_name(provider);
}
void bench_aes_cleanup(void) { EVP_CIPHER_free(cipher); cipher = NULL; }
const bench_backend bench_aes_blocks = {
    "AES-256-ECB/16B-updates", "EVP_CipherUpdate per 16 bytes; padding off", create, destroy, process_blocks, finish
};
const bench_backend bench_aes_batch = {
    "AES-256-ECB/batch-update", "one EVP_CipherUpdate per buffer; padding off", create, destroy, process_batch, finish
};
