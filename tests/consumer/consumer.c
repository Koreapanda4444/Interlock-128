#include <interlock.h>
#include <stdio.h>
#include <string.h>
int main(void) {
    const uint8_t key[32] = {0}, plaintext[16] = {0};
    const uint8_t expected[16] = {0x46,0x27,0x2f,0x40,0x86,0xf4,0x71,0xad,0x8a,0x7e,0xc9,0xc9,0x91,0x79,0x12,0xbb};
    uint8_t ciphertext[16], recovered[16];
    interlock_key_ctx *ctx = NULL;
    if (interlock_key_ctx_create(&ctx,key,sizeof(key)) != INTERLOCK_OK) return 1;
    if (interlock_encrypt_block(ctx,plaintext,sizeof(plaintext),ciphertext,sizeof(ciphertext)) != INTERLOCK_OK ||
        memcmp(ciphertext,expected,sizeof(expected)) != 0) {
        interlock_key_ctx_free(ctx); return 2;
    }
    if (interlock_decrypt_block(ctx,ciphertext,sizeof(ciphertext),recovered,sizeof(recovered)) != INTERLOCK_OK ||
        memcmp(recovered,plaintext,sizeof(plaintext)) != 0) {
        interlock_key_ctx_free(ctx); return 3;
    }
    interlock_key_ctx_free(ctx); ctx = NULL;
    puts("installed public-header consumer passed");
    return 0;
}
