#include "fk_asm.h"

long answer(void) ASM_FUNCTION(answer);
const char *greeting(void) ASM_FUNCTION(greeting);

TEST(answer_is_42) {
    EXPECT_EQ_INT(answer(), 42);
}

TEST(greets_the_world) {
    EXPECT_EQ_STR(greeting(), "Hello, World!");
}
