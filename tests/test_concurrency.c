#include "interlock.h"
#include "test_common.h"
#include <string.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <pthread.h>
#endif
typedef struct { const interlock_key_ctx *ctx; unsigned id; int failed; } job;
static void exercise(job *work) {
    const uint8_t expected[16] = {0x46,0x27,0x2f,0x40,0x86,0xf4,0x71,0xad,0x8a,0x7e,0xc9,0xc9,0x91,0x79,0x12,0xbb};
    uint8_t input[16] = {0}, output[16], recovered[16];
    uint32_t random = UINT32_C(20261109) ^ (uint32_t)work->id;
    if (interlock_encrypt_block(work->ctx,input,16,output,16) != INTERLOCK_OK || memcmp(output,expected,16) != 0) {
        work->failed = 1; return;
    }
    for (unsigned i = 0; i < 4096; ++i) {
        for (size_t j = 0; j < 16; ++j) {
            random = random * UINT32_C(1664525) + UINT32_C(1013904223);
            input[j] = (uint8_t)(random >> 24);
        }
        if (interlock_encrypt_block(work->ctx,input,16,output,16) != INTERLOCK_OK ||
            interlock_decrypt_block(work->ctx,output,16,recovered,16) != INTERLOCK_OK ||
            memcmp(input,recovered,16) != 0) { work->failed = 1; return; }
    }
}
#ifdef _WIN32
static DWORD WINAPI worker(LPVOID p) { exercise((job*)p); return 0; }
#else
static void *worker(void *p) { exercise((job*)p); return NULL; }
#endif
int main(void) {
    const uint8_t key[32] = {0};
    interlock_key_ctx *ctx = NULL;
    job jobs[4];
#ifdef _WIN32
    HANDLE threads[4];
#else
    pthread_t threads[4];
#endif
    CHECK(interlock_key_ctx_create(&ctx,key,32) == INTERLOCK_OK);
    for (unsigned j = 0; j < 4; ++j) {
        jobs[j].ctx = ctx; jobs[j].id = j; jobs[j].failed = 0;
#ifdef _WIN32
        threads[j] = CreateThread(NULL,0,worker,&jobs[j],0,NULL);
        CHECK(threads[j] != NULL);
#else
        CHECK(pthread_create(&threads[j],NULL,worker,&jobs[j]) == 0);
#endif
    }
    for (unsigned j = 0; j < 4; ++j) {
#ifdef _WIN32
        CHECK(WaitForSingleObject(threads[j],INFINITE) == WAIT_OBJECT_0);
        CHECK(CloseHandle(threads[j]));
#else
        CHECK(pthread_join(threads[j],NULL) == 0);
#endif
        CHECK(jobs[j].failed == 0);
    }
    interlock_key_ctx_free(ctx); ctx = NULL;
    return 0;
}
