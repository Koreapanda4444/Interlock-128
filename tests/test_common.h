#ifndef INTERLOCK_TEST_COMMON_H
#define INTERLOCK_TEST_COMMON_H
#include <stdio.h>
#include <stdlib.h>
#define CHECK(expr) do { if (!(expr)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #expr); exit(EXIT_FAILURE); } } while (0)
#endif
