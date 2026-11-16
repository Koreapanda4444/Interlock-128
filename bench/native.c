#if !defined(_WIN32)
#define _POSIX_C_SOURCE 200809L
#endif
#include "backend.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <openssl/crypto.h>
#ifdef _WIN32
#include <windows.h>
#endif

static volatile uint64_t sink = 0;
static void fail(const char *message) { fprintf(stderr, "%s\n", message); exit(1); }
static double now(void) {
#ifdef _WIN32
    LARGE_INTEGER count, frequency;
    if (!QueryPerformanceFrequency(&frequency) || !QueryPerformanceCounter(&count)) fail("QPC failed");
    return (double)count.QuadPart / (double)frequency.QuadPart;
#else
    struct timespec stamp;
    if (clock_gettime(CLOCK_MONOTONIC, &stamp) != 0) fail("monotonic clock failed");
    return (double)stamp.tv_sec + (double)stamp.tv_nsec * 1e-9;
#endif
}
static void consume(const uint8_t *data, size_t bytes) {
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t j = 0; j < bytes; ++j) hash = (hash ^ data[j]) * UINT64_C(1099511628211);
    sink = sink ^ hash;
}
static void json_string(const char *s) {
    putchar('"');
    if (s != NULL) for (; *s; ++s) {
        unsigned char c = (unsigned char)*s;
        if (c == '"' || c == '\\') { putchar('\\'); putchar(c); }
        else if (c < 32) printf("\\u%04x", (unsigned)c);
        else putchar(c);
    }
    putchar('"');
}

enum cost { READY, CREATE, FREE, FRESH };
static const uint8_t key[32] = {0};
static double measure(const bench_backend *b, enum cost cost, int decrypt,
                      size_t bytes, size_t iterations, void *ready,
                      const uint8_t *input, uint8_t *output) {
    void **contexts = NULL;
    double start, elapsed;
    if (cost == CREATE || cost == FREE) {
        contexts = calloc(iterations, sizeof(*contexts));
        if (contexts == NULL) fail("context pointer array allocation failed");
    }
    if (cost == FREE) for (size_t j = 0; j < iterations; ++j)
        if (!b->create(&contexts[j], key, decrypt)) fail("prepare free sample failed");
    start = now();
    for (size_t j = 0; j < iterations; ++j) {
        if (cost == READY) {
            if (!b->process(ready, decrypt, input, output, bytes)) fail("block processing failed");
        } else if (cost == CREATE) {
            if (!b->create(&contexts[j], key, decrypt)) fail("key preparation failed");
        } else if (cost == FREE) {
            b->destroy(contexts[j]);
        } else {
            void *ctx = NULL;
            if (!b->create(&ctx, key, 0)) fail("fresh key creation failed");
            if (!b->process(ctx, 0, input, output, 16)) fail("fresh block failed");
            if (b->finish != NULL && !b->finish(ctx)) fail("fresh final failed");
            b->destroy(ctx);
        }
    }
    elapsed = now() - start;
    if (cost == CREATE) for (size_t j = 0; j < iterations; ++j) b->destroy(contexts[j]);
    free(contexts);
    if (cost == READY || cost == FRESH) consume(output, cost == FRESH ? 16 : bytes);
    else sink = sink ^ (uint64_t)iterations;
    /* A single untimed warmup can be shorter than the clock's resolution. */
    if (elapsed < 0) fail("monotonic clock moved backwards");
    return elapsed;
}

static void verify(const bench_backend *b, void *enc, void *dec,
                   uint8_t *plain, uint8_t *cipher, uint8_t *recovered, size_t bytes) {
    if (!b->process(enc, 0, plain, cipher, bytes) || !b->process(dec, 1, cipher, recovered, bytes)
        || memcmp(plain, recovered, bytes) != 0) fail("benchmark roundtrip failed");
    if (b == &bench_interlock) {
        static const uint8_t expected[16] = {0x46,0x27,0x2f,0x40,0x86,0xf4,0x71,0xad,
                                           0x8a,0x7e,0xc9,0xc9,0x91,0x79,0x12,0xbb};
        uint8_t zero[16] = {0}, out[16];
        if (!b->process(enc, 0, zero, out, 16) || memcmp(out, expected, 16) != 0)
            fail("benchmark fixed KAT failed");
    }
}

static void row(const bench_backend *b, enum cost cost, int decrypt, size_t bytes,
                unsigned samples, double target, void *ready, const uint8_t *input,
                uint8_t *output, int *first) {
    const char *name = cost == READY ? (decrypt ? "decrypt_ready" : "encrypt_ready") :
                       cost == CREATE ? "key_create" : cost == FREE ? "key_free" : "fresh_key_encrypt_free";
    size_t iterations = 1, limit = cost == CREATE || cost == FREE ? 8192 : 1048576;
    /* Warmup and calibration are excluded from all reported samples. */
    for (unsigned warm = 0; warm < 3; ++warm) measure(b,cost,decrypt,bytes,1,ready,input,output);
    for (;;) {
        double elapsed = measure(b,cost,decrypt,bytes,iterations,ready,input,output);
        if (elapsed >= target || iterations >= limit) break;
        iterations = iterations > limit/2 ? limit : iterations*2;
    }
    if (!*first) putchar(',');
    *first = 0;
    printf("{\"backend\":"); json_string(b->name);
    printf(",\"calls\":"); json_string(b->calls);
    printf(",\"operation\":\"%s\",\"bytes_per_iteration\":%zu,\"warmup_iterations\":3,\"samples\":[",
           name, cost == CREATE || cost == FREE ? 0 : bytes);
    for (unsigned s = 0; s < samples; ++s) {
        double elapsed = measure(b,cost,decrypt,bytes,iterations,ready,input,output);
        while (elapsed == 0 && iterations < limit) {
            iterations = iterations > limit/2 ? limit : iterations*2;
            elapsed = measure(b,cost,decrypt,bytes,iterations,ready,input,output);
        }
        if (elapsed <= 0) fail("clock resolution insufficient even at iteration limit");
        if (s) putchar(',');
        printf("{\"iterations\":%zu,\"elapsed_seconds\":%.9f}", iterations, elapsed);
    }
    printf("]}");
}

int main(int argc, char **argv) {
    unsigned samples = 5;
    double target = 0.04;
    const size_t sizes[] = {16,1024,16384,1048576};
    const bench_backend *backends[] = {&bench_interlock,&bench_aes_blocks,&bench_aes_batch};
    uint8_t *plain, *cipher, *output;
    int first = 1;
    for (int j = 1; j < argc; ++j) {
        char *end = NULL;
        if (strcmp(argv[j], "--samples") == 0 && j+1 < argc) {
            unsigned long n = strtoul(argv[++j], &end, 10);
            if (*end || n < 5 || n > 100) fail("samples must be 5..100");
            samples = (unsigned)n;
        } else if (strcmp(argv[j], "--target-ms") == 0 && j+1 < argc) {
            double ms = strtod(argv[++j], &end);
            if (*end || !(ms >= 1 && ms <= 1000)) fail("target-ms must be 1..1000");
            target = ms/1000;
        } else fail("usage: interlock_bench [--samples 5..100] [--target-ms 1..1000]");
    }
    plain = malloc(1048576); cipher = malloc(1048576); output = malloc(1048576);
    if (!plain || !cipher || !output) fail("data allocation failed");
    for (size_t j = 0; j < 1048576; ++j) plain[j] = (uint8_t)(j*37u + j/256u);
    if (!bench_aes_init()) fail("AES fetch or FIPS197 KAT failed");
    printf("{\"schema_version\":1,\"status\":\"complete\",\"correctness\":\"KAT and all-size roundtrips\",\"timer\":");
#ifdef _WIN32
    json_string("QueryPerformanceCounter");
#else
    json_string("clock_gettime(CLOCK_MONOTONIC)");
#endif
    printf(",\"openssl\":"); json_string(OpenSSL_version(OPENSSL_VERSION));
    printf(",\"cpu_settings\":"); json_string(OpenSSL_version(OPENSSL_CPU_INFO));
    printf(",\"aes_provider\":"); json_string(bench_aes_provider());
    printf(",\"target_seconds\":%.6f,\"rows\":[", target);
    for (size_t i = 0; i < sizeof(backends)/sizeof(backends[0]); ++i) {
        const bench_backend *b = backends[i];
        void *enc = NULL, *dec = NULL;
        if (!b->create(&enc,key,0) || !b->create(&dec,key,1)) fail("ready key creation failed");
        row(b,CREATE,0,0,samples,target,enc,plain,output,&first);
        row(b,FREE,0,0,samples,target,enc,plain,output,&first);
        row(b,FRESH,0,16,samples,target,enc,plain,output,&first);
        for (size_t z = 0; z < sizeof(sizes)/sizeof(sizes[0]); ++z) {
            size_t bytes = sizes[z];
            verify(b,enc,dec,plain,cipher,output,bytes);
            row(b,READY,0,bytes,samples,target,enc,plain,output,&first);
            if (memcmp(output,cipher,bytes) != 0) fail("timed encryption mismatch");
            row(b,READY,1,bytes,samples,target,dec,cipher,output,&first);
            if (memcmp(output,plain,bytes) != 0) fail("timed decryption mismatch");
        }
        if (b->finish != NULL && (!b->finish(dec) || !b->finish(enc))) fail("ready final failed");
        b->destroy(dec); b->destroy(enc);
    }
    printf("],\"checksum\":\"%016" PRIx64 "\"}\n", sink);
    free(output); free(cipher); free(plain);
    bench_aes_cleanup();
    return 0;
}
