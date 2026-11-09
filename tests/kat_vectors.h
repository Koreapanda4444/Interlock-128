#ifndef INTERLOCK_KAT_VECTORS_H
#define INTERLOCK_KAT_VECTORS_H
#include <stdint.h>
#include <stddef.h>
#include "test_common.h"
typedef struct { const char *key, *plaintext, *ciphertext; } kat_vector;
static const kat_vector kats[] = {
    {"0000000000000000000000000000000000000000000000000000000000000000",
     "00000000000000000000000000000000", "46272f4086f471ad8a7ec9c9917912bb"},
    {"000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
     "000102030405060708090a0b0c0d0e0f", "55b8e32c0f8b46ab083cb4a21150c3e8"},
    {"ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "ffffffffffffffffffffffffffffffff", "f8c5d0db5d69b06a2ef4398b6b4f55d6"},
    {"0000000000000000000000000000000000000000000000000000000000000000",
     "01000000000000000000000000000000", "52e7cbd4aa223cdbf3232c0f9c1b75e0"}
};
static void kat_decode(const char *hex, uint8_t *out, size_t n) {
    for (size_t j = 0; j < n; ++j) {
        unsigned x;
        CHECK(sscanf(hex+2*j, "%2x", &x) == 1);
        out[j] = (uint8_t)x;
    }
}
#endif
