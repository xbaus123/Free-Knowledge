/*
 * FreeKnowledge test harness for assembly lessons: C tests that call the
 * learner's x86-64 functions.
 *
 *   #include "fk_asm.h"
 *   long add(long a, long b) ASM_FUNCTION(add);
 *   TEST(adds_small_numbers) { EXPECT_EQ_INT(add(2, 3), 5); }
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

#endif
