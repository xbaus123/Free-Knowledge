/*
 * FreeKnowledge test harness for assembly lessons: C tests that call the
 * learner's x86-64 functions.
 *
 *   #include "fk_asm.h"
 *   long add(long a, long b) ASM_FUNCTION(add);
 *   TEST(adds_small_numbers) { EXPECT_EQ_INT(add(2, 3), 5); }
 *   TEST(add_preserves_registers) { EXPECT_PRESERVES(add, (2, 3)); }
 *
 * ASM_FUNCTION links the declaration to the label exactly as written (macOS
 * would otherwise look for _add) and calls it with the System V convention
 * (arguments in rdi, rsi, rdx, rcx, r8, r9) on every platform, Windows
 * included.
 */
#ifndef FK_ASM_H
#define FK_ASM_H

#include "fk_test.h"

#define ASM_FUNCTION(name) __asm__(#name) __attribute__((sysv_abi))

/* fk_check.s */
extern const void *fk_check_target __asm__("fk_check_target");
extern unsigned long fk_check_clobbered __asm__("fk_check_clobbered");
void fk_check_trampoline(void) __asm__("fk_check_trampoline");

/*
 * EXPECT_PRESERVES(fn, (args)) calls fn with args (register arguments only,
 * at most six) and fails if it changed a register its caller relies on:
 * rbx, rbp, r12 to r15, or rsp.
 */
#define EXPECT_PRESERVES(fn, args)                                  \
    do {                                                            \
        fk_check_target = (const void *)&fn;                        \
        fk_check_clobbered = 0;                                     \
        ((__typeof__(&fn))fk_check_trampoline) args;                \
        fk_report_clobbered(__FILE__, __LINE__, #fn #args);         \
    } while (0)

static void fk_report_clobbered(const char *file, int line, const char *call) {
    static const char *names[] = {"rbx", "rbp", "r12", "r13", "r14", "r15", "rsp"};
    char changed[64] = "";
    for (int i = 0; i < 7; i++) {
        if (fk_check_clobbered & (1UL << i)) {
            if (changed[0]) strcat(changed, ", ");
            strcat(changed, names[i]);
        }
    }
    if (!changed[0]) return;
    fk_fail(file, line,
            "%s changed %s without restoring it. Its caller expects these registers back unchanged: "
            "use rax, rcx, rdx, rsi, rdi, or r8 to r11 for scratch values, or save the register with push and restore it with pop.",
            call, changed);
}

#endif
