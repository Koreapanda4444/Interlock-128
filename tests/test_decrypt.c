#include "interlock.h"
#include "test_common.h"
#include "kat_vectors.h"
#include <string.h>
static void untouched(const uint8_t *p, size_t n) {
    for (size_t j = 0; j < n; ++j) CHECK(p[j] == 0xa5);
}
int main(void) {
    for (size_t v = 0; v < sizeof(kats)/sizeof(kats[0]); ++v) {
        uint8_t key[32], plaintext[16], ciphertext[16], input[18], output[34], buffer[64], saved[64];
        interlock_key_ctx *ctx = NULL;
        const size_t lengths[] = {0,1,15,17,SIZE_MAX};
        const size_t capacities[] = {0,15};
        kat_decode(kats[v].key, key, 32); kat_decode(kats[v].plaintext, plaintext, 16);
        kat_decode(kats[v].ciphertext, ciphertext, 16);
        CHECK(interlock_key_ctx_create(&ctx, key, 32) == INTERLOCK_OK);
        memset(input, 0xa5, sizeof(input)); memcpy(input+1, ciphertext, 16);
        memset(output, 0xa5, sizeof(output));
        CHECK(interlock_decrypt_block(ctx, input+1, 16, output+1, 33) == INTERLOCK_OK);
        CHECK(memcmp(output+1, plaintext, 16) == 0);
        CHECK(output[0] == 0xa5); untouched(output+17, 17);
        CHECK(input[0] == 0xa5 && input[17] == 0xa5 && memcmp(input+1, ciphertext, 16) == 0);
        memset(output, 0xa5, sizeof(output)); memcpy(output+1, ciphertext, 16);
        CHECK(interlock_decrypt_block(ctx, output+1, 16, output+1, 33) == INTERLOCK_OK);
        CHECK(memcmp(output+1, plaintext, 16) == 0);
        CHECK(interlock_encrypt_block(ctx, output+1, 16, output+1, 33) == INTERLOCK_OK);
        CHECK(memcmp(output+1, ciphertext, 16) == 0);
        CHECK(output[0] == 0xa5); untouched(output+17, 17);
        memset(output, 0xa5, sizeof(output)); memcpy(output+1, plaintext, 16);
        CHECK(interlock_encrypt_block(ctx, output+1, 16, output+1, 33) == INTERLOCK_OK);
        CHECK(memcmp(output+1, ciphertext, 16) == 0);
        CHECK(interlock_decrypt_block(ctx, output+1, 16, output+1, 33) == INTERLOCK_OK);
        CHECK(memcmp(output+1, plaintext, 16) == 0);
        CHECK(output[0] == 0xa5); untouched(output+17, 17);
        memset(output, 0xa5, sizeof(output));
        CHECK(interlock_decrypt_block(NULL, ciphertext, 16, output, 34) == INTERLOCK_EINVAL);
        CHECK(interlock_decrypt_block(ctx, NULL, 16, output, 34) == INTERLOCK_EINVAL);
        CHECK(interlock_decrypt_block(ctx, ciphertext, 16, NULL, 34) == INTERLOCK_EINVAL);
        untouched(output, sizeof(output));
        for (size_t j = 0; j < sizeof(lengths)/sizeof(lengths[0]); ++j) {
            CHECK(interlock_decrypt_block(ctx, ciphertext, lengths[j], output, 34) == INTERLOCK_ELENGTH);
            untouched(output, sizeof(output));
        }
        for (size_t j = 0; j < sizeof(capacities)/sizeof(capacities[0]); ++j) {
            CHECK(interlock_decrypt_block(ctx, ciphertext, 16, output, capacities[j]) == INTERLOCK_ECAPACITY);
            untouched(output, sizeof(output));
        }
        for (int delta = -15; delta <= 15; ++delta) {
            if (delta == 0) continue;
            memset(buffer, 0xa5, sizeof(buffer)); memcpy(buffer+24, ciphertext, 16);
            memcpy(saved, buffer, sizeof(saved));
            CHECK(interlock_decrypt_block(ctx, buffer+24, 16, buffer+24+delta, 16) == INTERLOCK_EOVERLAP);
            CHECK(memcmp(buffer, saved, sizeof(buffer)) == 0);
        }
        for (size_t cap = 16; cap <= 17; ++cap) {
            memset(output, 0xa5, sizeof(output));
            CHECK(interlock_decrypt_block(ctx, ciphertext, 16, output, cap) == INTERLOCK_OK);
            CHECK(memcmp(output, plaintext, 16) == 0); untouched(output+16, 18);
        }
        memcpy(buffer, ciphertext, 16);
        CHECK(interlock_decrypt_block(ctx, buffer, 16, buffer+16, 16) == INTERLOCK_OK);
        CHECK(memcmp(buffer+16, plaintext, 16) == 0 && memcmp(buffer, ciphertext, 16) == 0);
        interlock_key_ctx_free(ctx); ctx = NULL;
    }
    return 0;
}
