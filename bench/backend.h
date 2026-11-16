#ifndef INTERLOCK_BENCH_BACKEND_H
#define INTERLOCK_BENCH_BACKEND_H
#include <stddef.h>
#include <stdint.h>
typedef struct {
    const char *name;
    const char *calls;
    int (*create)(void **ctx, const uint8_t key[32], int decrypt);
    void (*destroy)(void *ctx);
    int (*process)(void *ctx, int decrypt, const uint8_t *in, uint8_t *out, size_t bytes);
    int (*finish)(void *ctx);
} bench_backend;
extern const bench_backend bench_interlock;
extern const bench_backend bench_aes_blocks, bench_aes_batch;
int bench_aes_init(void);
const char *bench_aes_provider(void);
void bench_aes_cleanup(void);
#endif
