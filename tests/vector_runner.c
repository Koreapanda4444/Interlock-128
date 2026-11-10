#include "interlock.h"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef IL_PREFIX_DRIVER
#include "internal.h"
#endif
static int hex_digit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
static int decode(const char *s, uint8_t *out, size_t n) {
    if (strlen(s) != 2*n) return 0;
    for (size_t j = 0; j < n; ++j) {
        int a = hex_digit(s[2*j]), b = hex_digit(s[2*j+1]);
        if (a < 0 || b < 0) return 0;
        out[j] = (uint8_t)(16*a+b);
    }
    return 1;
}
static int process(char *line) {
    char *operation = strtok(line, " \t\r\n"), *count, *key_hex, *block_hex, *end;
    unsigned long rounds;
    uint8_t key[32], input[16], output[448];
    size_t output_length = 16;
    int decrypt;
    if (operation == NULL) return 0;
    count = strtok(NULL, " \t\r\n"); key_hex = strtok(NULL, " \t\r\n");
    block_hex = strtok(NULL, " \t\r\n");
    if (count == NULL || key_hex == NULL || block_hex == NULL || strtok(NULL, " \t\r\n") != NULL) return 0;
    if (count[0] == '\0') return 0;
    for (const char *p = count; *p != '\0'; ++p) if (*p < '0' || *p > '9') return 0;
    errno = 0; rounds = strtoul(count, &end, 10);
    if (errno != 0 || *end != '\0' || rounds > 28 || !decode(key_hex, key, 32) || !decode(block_hex, input, 16)) return 0;
    decrypt = strcmp(operation, "dec") == 0;
#ifdef IL_PREFIX_DRIVER
    {
        uint32_t schedule[28][4], state[4];
        int keys = strcmp(operation, "keys") == 0;
        if (!decrypt && strcmp(operation, "enc") != 0 && !keys) return 0;
        if (keys && rounds != 28) return 0;
        if (il_expand_key(key, sizeof(key), schedule) != 1) return 0;
        if (keys) {
            output_length = 448;
            for (size_t r = 0; r < 28; ++r)
                for (size_t j = 0; j < 4; ++j) il_store32(output+16*r+4*j, schedule[r][j]);
        } else {
            for (size_t j = 0; j < 4; ++j) state[j] = il_load32(input+4*j);
            if (decrypt) {
                for (size_t r = (size_t)rounds; r-- > 0;) il_test_reverse_round(state, schedule[r]);
            } else {
                for (size_t r = 0; r < (size_t)rounds; ++r) il_test_forward_round(state, schedule[r]);
            }
            for (size_t j = 0; j < 4; ++j) il_store32(output+4*j, state[j]);
            il_cleanse(state, sizeof(state));
        }
        il_cleanse(schedule, sizeof(schedule));
    }
#else
    {
        interlock_key_ctx *ctx = NULL;
        interlock_status status;
        if (rounds != 28 || (!decrypt && strcmp(operation, "enc") != 0)) return 0;
        if (interlock_key_ctx_create(&ctx, key, sizeof(key)) != INTERLOCK_OK) return 0;
        status = decrypt ? interlock_decrypt_block(ctx, input, 16, output, sizeof(output)) :
                           interlock_encrypt_block(ctx, input, 16, output, sizeof(output));
        interlock_key_ctx_free(ctx);
        if (status != INTERLOCK_OK) return 0;
    }
#endif
    for (size_t j = 0; j < output_length; ++j) printf("%02x", (unsigned)output[j]);
    putchar('\n');
    return 1;
}
int main(void) {
    char line[1024];
    int had_error = 0;
    while (fgets(line, sizeof(line), stdin) != NULL) {
        if (strchr(line, '\n') == NULL && !feof(stdin)) {
            int c;
            while ((c = getchar()) != '\n' && c != EOF) { }
            puts("ERR"); had_error = 1; continue;
        }
        if (!process(line)) { puts("ERR"); had_error = 1; }
    }
    return ferror(stdin) || ferror(stdout) || had_error ? EXIT_FAILURE : EXIT_SUCCESS;
}
