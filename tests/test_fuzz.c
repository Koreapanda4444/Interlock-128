#include "interlock.h"
#include "test_common.h"
#include <stdio.h>
#include <string.h>
typedef interlock_status (*block_function)(const interlock_key_ctx*,const uint8_t*,size_t,uint8_t*,size_t);
static uint32_t next(uint32_t *state) {
    *state = *state * UINT32_C(1664525) + UINT32_C(1013904223);
    return *state;
}
int main(void) {
    uint32_t random = UINT32_C(20261109);
    const size_t lengths[] = {0,1,15,16,17,SIZE_MAX};
    const size_t capacities[] = {0,15,16,17};
    unsigned counts[7] = {0};
    interlock_key_ctx *ctx = NULL;
    for (unsigned i = 0; i < 16384; ++i) {
        uint8_t buffer[128], saved[128], expected_buffer[128], expected[16];
        const uint8_t *input;
        uint8_t *output;
        const interlock_key_ctx *selected;
        block_function function;
        size_t length, capacity;
        int offset, valid;
        interlock_status status;
        if (i % 256 == 0) {
            uint8_t key[32];
            interlock_key_ctx_free(ctx); ctx = NULL;
            for (size_t j = 0; j < 32; ++j) key[j] = (uint8_t)(next(&random) >> 24);
            CHECK(interlock_key_ctx_create(&ctx,key,32) == INTERLOCK_OK);
        }
        for (size_t j = 0; j < sizeof(buffer); ++j) buffer[j] = (uint8_t)(next(&random) >> 24);
        memcpy(saved,buffer,sizeof(buffer)); memcpy(expected_buffer,buffer,sizeof(buffer));
        offset = (int)((next(&random) >> 16) % 41)-20;
        length = lengths[(next(&random) >> 16) % 6];
        capacity = capacities[(next(&random) >> 16) % 4];
        input = ((next(&random) >> 16) % 8) == 0 ? NULL : buffer+48;
        output = ((next(&random) >> 16) % 8) == 0 ? NULL : buffer+48+offset;
        selected = ((next(&random) >> 16) % 8) == 0 ? NULL : ctx;
        function = ((next(&random) >> 16) & 1u) ? interlock_encrypt_block : interlock_decrypt_block;
        if (i % 8 == 0) {
            length = 16; capacity = 16; offset = i % 16 == 0 ? 0 : 20;
            input = buffer+48; output = buffer+48+offset; selected = ctx;
        }
        valid = selected != NULL && input != NULL && output != NULL && length == 16 && capacity >= 16 &&
                (offset == 0 || offset <= -16 || offset >= 16);
        if (valid) {
            CHECK(function(ctx,buffer+48,16,expected,16) == INTERLOCK_OK);
            memcpy(expected_buffer+48+offset,expected,16);
        }
        status = function(selected,input,length,output,capacity);
        CHECK(status >= INTERLOCK_OK && status <= INTERLOCK_ECRYPTO);
        ++counts[(unsigned)status];
        if ((valid && (status != INTERLOCK_OK || memcmp(buffer,expected_buffer,sizeof(buffer)) != 0)) ||
            (!valid && (status == INTERLOCK_OK || memcmp(buffer,saved,sizeof(buffer)) != 0))) {
            fprintf(stderr,"seed=20261109 case=%u length=%zu capacity=%zu offset=%d status=%d\n",
                    i,length,capacity,offset,(int)status);
            interlock_key_ctx_free(ctx);
            return 1;
        }
    }
    interlock_key_ctx_free(ctx); ctx = NULL;
    for (unsigned j = 0; j <= INTERLOCK_EOVERLAP; ++j) CHECK(counts[j] != 0);
    printf("{\"seed\":20261109,\"cases\":16384,\"statuses\":[%u,%u,%u,%u,%u,%u,%u]}\n",
           counts[0],counts[1],counts[2],counts[3],counts[4],counts[5],counts[6]);
    return 0;
}
