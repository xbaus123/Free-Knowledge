/*
 * FreeKnowledge test harness for C lessons.
 *
 *   #include "fk_test.h"
 *   int add(int a, int b);
 *   TEST(adds_small_numbers) { EXPECT_EQ_INT(add(2, 3), 5); }
 *
 * Results are appended to $FK_RESULTS as JSON lines. A "run" record is
 * written before each test so a crash is attributed to the right test.
 */
#ifndef FK_TEST_H
#define FK_TEST_H

#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef void (*fk_test_fn)(void);

#define FK_MAX_TESTS 256

static struct {
    const char *name;
    fk_test_fn fn;
} fk_tests[FK_MAX_TESTS];
static int fk_test_count;
static int fk_failed;
static char fk_message[2048];

static void fk_register(const char *name, fk_test_fn fn) {
    if (fk_test_count < FK_MAX_TESTS) {
        fk_tests[fk_test_count].name = name;
        fk_tests[fk_test_count].fn = fn;
        fk_test_count++;
    }
}

#define TEST(name)                                                      \
    static void name(void);                                             \
    __attribute__((constructor)) static void fk_register_##name(void) { \
        fk_register(#name, name);                                       \
    }                                                                   \
    static void name(void)

static void fk_fail(const char *file, int line, const char *fmt, ...) {
    size_t used = strlen(fk_message);
    if (!fk_failed) used = 0;
    fk_failed = 1;
    if (used >= sizeof fk_message - 1) return;
    int n = snprintf(fk_message + used, sizeof fk_message - used, "%s%s:%d: ", used ? "\n" : "", file, line);
    if (n < 0) return;
    used += (size_t)n;
    if (used >= sizeof fk_message) return;
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(fk_message + used, sizeof fk_message - used, fmt, ap);
    va_end(ap);
}

#define EXPECT_TRUE(cond) \
    do { if (!(cond)) fk_fail(__FILE__, __LINE__, "expected %s to be true", #cond); } while (0)

#define EXPECT_EQ_INT(actual, expected)                                                    \
    do {                                                                                   \
        long long fk_a = (long long)(actual), fk_e = (long long)(expected);                \
        if (fk_a != fk_e)                                                                  \
            fk_fail(__FILE__, __LINE__, "%s: got %lld, want %lld", #actual, fk_a, fk_e);   \
    } while (0)

#define EXPECT_EQ_DOUBLE(actual, expected, eps)                                            \
    do {                                                                                   \
        double fk_a = (double)(actual), fk_e = (double)(expected);                         \
        if (fabs(fk_a - fk_e) > (eps))                                                     \
            fk_fail(__FILE__, __LINE__, "%s: got %g, want %g", #actual, fk_a, fk_e);       \
    } while (0)

#define EXPECT_EQ_STR(actual, expected)                                                    \
    do {                                                                                   \
        const char *fk_a = (actual), *fk_e = (expected);                                   \
        if (!fk_a || !fk_e || strcmp(fk_a, fk_e) != 0)                                     \
            fk_fail(__FILE__, __LINE__, "%s: got \"%s\", want \"%s\"", #actual,            \
                    fk_a ? fk_a : "(null)", fk_e ? fk_e : "(null)");                       \
    } while (0)

static void fk_write_json_string(FILE *f, const char *s) {
    fputc('"', f);
    for (; *s; s++) {
        unsigned char c = (unsigned char)*s;
        if (c == '"' || c == '\\') fprintf(f, "\\%c", c);
        else if (c == '\n') fputs("\\n", f);
        else if (c == '\t') fputs("\\t", f);
        else if (c < 0x20) fprintf(f, "\\u%04x", c);
        else fputc(c, f);
    }
    fputc('"', f);
}

static void fk_record(const char *name, const char *status, const char *message, long ms) {
    const char *path = getenv("FK_RESULTS");
    FILE *f = path ? fopen(path, "a") : NULL;
    if (!f) return;
    fputs("{\"name\":", f);
    fk_write_json_string(f, name);
    fprintf(f, ",\"status\":\"%s\",\"message\":", status);
    fk_write_json_string(f, message);
    fprintf(f, ",\"durationMs\":%ld}\n", ms);
    fclose(f);
}

int main(void) {
    int any_failed = 0;
    for (int i = 0; i < fk_test_count; i++) {
        fk_failed = 0;
        fk_message[0] = '\0';
        fk_record(fk_tests[i].name, "run", "", 0);
        clock_t start = clock();
        fk_tests[i].fn();
        fflush(stdout);
        long ms = (long)((clock() - start) * 1000 / CLOCKS_PER_SEC);
        fk_record(fk_tests[i].name, fk_failed ? "fail" : "pass", fk_message, ms);
        any_failed |= fk_failed;
    }
    return any_failed;
}

#endif
