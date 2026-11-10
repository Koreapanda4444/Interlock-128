#include "interlock.h"
#include "internal.h"
#include "test_common.h"
#include "kat_vectors.h"
#include <stdlib.h>
#include <string.h>
typedef interlock_status (*block_function)(const interlock_key_ctx*, const uint8_t*, size_t, uint8_t*, size_t);
static void check_buffers(block_function function, const interlock_key_ctx *ctx,
                          const uint8_t source[16], const uint8_t expected[16]) {
    const size_t lengths[] = {0,1,15,16,17,SIZE_MAX};
    const size_t capacities[] = {0,15,16,17};
    for (size_t li = 0; li < sizeof(lengths)/sizeof(lengths[0]); ++li) {
        for (size_t ci = 0; ci < sizeof(capacities)/sizeof(capacities[0]); ++ci) {
            size_t n = lengths[li], capacity = capacities[ci];
            size_t actual_input = n == SIZE_MAX ? 17 : n == 0 ? 1 : n;
            size_t actual_output = capacity == 0 ? 1 : capacity;
            uint8_t *input = malloc(actual_input+2), *output = malloc(actual_output+2);
            interlock_status result;
            CHECK(input != NULL && output != NULL);
            memset(input,0xa5,actual_input+2); memset(output,0xa5,actual_output+2);
            memcpy(input+1,source,actual_input < 16 ? actual_input : 16);
            result = function(ctx,input+1,n,output+1,capacity);
            if (n != 16) CHECK(result == INTERLOCK_ELENGTH);
            else if (capacity < 16) CHECK(result == INTERLOCK_ECAPACITY);
            else CHECK(result == INTERLOCK_OK && memcmp(output+1,expected,16) == 0);
            CHECK(input[0] == 0xa5 && input[actual_input+1] == 0xa5);
            CHECK(memcmp(input+1,source,actual_input < 16 ? actual_input : 16) == 0);
            for (size_t j = 0; j < actual_output+2; ++j)
                if (result != INTERLOCK_OK || j < 1 || j > 16) CHECK(output[j] == 0xa5);
            free(input); free(output);
        }
    }
    for (int offset = -32; offset <= 32; ++offset) {
        uint8_t buffer[96], original[96], expected_buffer[96];
        interlock_status status;
        memset(buffer,0xa5,sizeof(buffer)); memcpy(buffer+32,source,16);
        memcpy(original,buffer,sizeof(buffer)); memcpy(expected_buffer,buffer,sizeof(buffer));
        status = function(ctx,buffer+32,16,buffer+32+offset,16);
        if (offset != 0 && offset > -16 && offset < 16) {
            CHECK(status == INTERLOCK_EOVERLAP);
            CHECK(memcmp(buffer,original,sizeof(buffer)) == 0);
        } else {
            CHECK(status == INTERLOCK_OK);
            memcpy(expected_buffer+32+offset,expected,16);
            CHECK(memcmp(buffer,expected_buffer,sizeof(buffer)) == 0);
        }
    }
    {
        uint8_t output[32];
        memset(output,0xa5,sizeof(output));
        CHECK(function(NULL,source,16,output,32) == INTERLOCK_EINVAL);
        CHECK(function(ctx,NULL,16,output,32) == INTERLOCK_EINVAL);
        CHECK(function(ctx,source,16,NULL,32) == INTERLOCK_EINVAL);
        for (size_t j = 0; j < sizeof(output); ++j) CHECK(output[j] == 0xa5);
        memcpy(output,source,16);
        CHECK(function(ctx,output,15,output,16) == INTERLOCK_ELENGTH);
        CHECK(memcmp(output,source,16) == 0);
    }
}
static void reset_observer(void) {
    il_test_cleanse_calls = 0; il_test_cleanse_bytes = 0; il_test_cleanse_zero = 1;
}
int main(void) {
    uint8_t key[33] = {0}, saved_key[33] = {0}, plain[16], cipher[16];
    const size_t bad_lengths[] = {0,1,31,33,SIZE_MAX};
    interlock_key_ctx *ctx = NULL;
    kat_decode(kats[0].plaintext,plain,16); kat_decode(kats[0].ciphertext,cipher,16);
    CHECK(interlock_key_ctx_create(&ctx,key,32) == INTERLOCK_OK);
    check_buffers(interlock_encrypt_block,ctx,plain,cipher);
    check_buffers(interlock_decrypt_block,ctx,cipher,plain);
    for (size_t j = 0; j < sizeof(bad_lengths)/sizeof(bad_lengths[0]); ++j) {
        interlock_key_ctx *existing = ctx, *empty = NULL;
        CHECK(interlock_key_ctx_create(&existing,key,bad_lengths[j]) != INTERLOCK_OK && existing == ctx);
        CHECK(interlock_key_ctx_create(&empty,key,bad_lengths[j]) == INTERLOCK_ELENGTH && empty == NULL);
    }
    {
        struct slot_object { uint8_t before[32]; interlock_key_ctx *slot; uint8_t after[64]; } object;
        uint8_t snapshot[sizeof(object)];
        size_t start = offsetof(struct slot_object,slot);
        for (size_t offset = start-31; offset < start+sizeof(object.slot); ++offset) {
            memset(&object,0,sizeof(object)); object.slot = NULL;
            memcpy(snapshot,&object,sizeof(object));
            CHECK(interlock_key_ctx_create(&object.slot,(const uint8_t*)&object+offset,32) == INTERLOCK_EOVERLAP);
            CHECK(memcmp(snapshot,&object,sizeof(object)) == 0);
        }
    }
    interlock_key_ctx_free(ctx); ctx = NULL;
    for (int failure = 1; failure <= 10; ++failure) {
        if (failure > 5 && failure < 10) continue;
        reset_observer(); il_test_failure = failure;
        CHECK(interlock_key_ctx_create(&ctx,key,32) ==
              (failure <= 2 || failure == 10 ? INTERLOCK_ENOMEM : INTERLOCK_ECRYPTO));
        CHECK(ctx == NULL && memcmp(key,saved_key,sizeof(key)) == 0);
        CHECK(il_test_cleanse_zero);
        if (failure == 10) CHECK(il_test_cleanse_calls == 0);
        else CHECK(il_test_cleanse_calls >= 2 && il_test_cleanse_bytes >= 896);
    }
    il_test_failure = 0; reset_observer();
    CHECK(interlock_key_ctx_create(&ctx,key,32) == INTERLOCK_OK);
    {
        size_t calls = il_test_cleanse_calls, bytes = il_test_cleanse_bytes;
        interlock_key_ctx_free(ctx); ctx = NULL;
        CHECK(il_test_cleanse_zero && il_test_cleanse_calls == calls+1);
        CHECK(il_test_cleanse_bytes == bytes+sizeof(struct interlock_key_ctx));
        calls = il_test_cleanse_calls;
        interlock_key_ctx_free(NULL);
        CHECK(il_test_cleanse_calls == calls);
    }
    return 0;
}
