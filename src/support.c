#include "internal.h"
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
