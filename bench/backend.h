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
} bench_backend;
extern const bench_backend bench_interlock;
#endif
