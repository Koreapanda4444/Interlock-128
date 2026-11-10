#include "internal.h"
#include <openssl/crypto.h>
#include <openssl/evp.h>
#include <string.h>
#ifdef INTERLOCK_TESTING
int il_test_failure = 0;
size_t il_test_cleanse_calls = 0;
size_t il_test_cleanse_bytes = 0;
int il_test_cleanse_zero = 1;
#endif
int il_range_end(uintptr_t start, size_t length, uintptr_t *end) {
    if (length > UINTPTR_MAX - start) return 0;
    *end = start + (uintptr_t)length;
    return 1;
}
int il_ranges_overlap(const void *a, size_t na, const void *b, size_t nb) {
    uintptr_t sa = (uintptr_t)a, sb = (uintptr_t)b, ea, eb;
    if (!il_range_end(sa, na, &ea) || !il_range_end(sb, nb, &eb)) return -1;
    return na != 0 && nb != 0 && sa < eb && sb < ea;
}
void il_cleanse(void *p, size_t length) {
    OPENSSL_cleanse(p, length);
#ifdef INTERLOCK_TESTING
    ++il_test_cleanse_calls;
    il_test_cleanse_bytes += length;
    for (size_t j = 0; j < length; ++j)
        if (((const volatile unsigned char*)p)[j] != 0) il_test_cleanse_zero = 0;
#endif
}
int il_shake256(const il_span *parts, size_t count, uint8_t *output, size_t length) {
    EVP_MD_CTX *ctx = NULL;
    uint8_t *temporary;
    int result = 0;
    if (output == NULL || length == 0 || (count != 0 && parts == NULL)) return -1;
    for (size_t i = 0; i < count; ++i) {
        if (parts[i].data == NULL && parts[i].length != 0) return -1;
    }
    temporary = IL_FAIL(1) ? NULL : OPENSSL_malloc(length);
    if (temporary == NULL) return -2;
    ctx = IL_FAIL(2) ? NULL : EVP_MD_CTX_new();
    if (ctx == NULL) { result = -2; goto done; }
    if (IL_FAIL(3) || EVP_DigestInit_ex(ctx, EVP_shake256(), NULL) != 1) goto done;
    for (size_t i = 0; i < count; ++i) {
        if (IL_FAIL(4) || (parts[i].length != 0 &&
            EVP_DigestUpdate(ctx, parts[i].data, parts[i].length) != 1)) goto done;
    }
    if (IL_FAIL(5) || EVP_DigestFinalXOF(ctx, temporary, length) != 1) goto done;
    memcpy(output, temporary, length);
    result = 1;
done:
    EVP_MD_CTX_free(ctx);
    il_cleanse(temporary, length);
    OPENSSL_free(temporary);
    return result;
}
