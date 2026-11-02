#include "fk_asm.h"

long linear(long a, long x, long b) ASM_FUNCTION(linear);
long low_byte(long x) ASM_FUNCTION(low_byte);

TEST(linear_small_numbers) {
    EXPECT_EQ_INT(linear(3, 4, 5), 17);
}

TEST(linear_negative_numbers) {
    EXPECT_EQ_INT(linear(-2, 7, -1), -15);
}

TEST(linear_uses_all_64_bits) {
    EXPECT_EQ_INT(linear(3000000000L, 4, 1), 12000000001L);
}

TEST(low_byte_of_small_number) {
    EXPECT_EQ_INT(low_byte(0x1234), 0x34);
}

TEST(low_byte_ignores_upper_bits) {
    EXPECT_EQ_INT(low_byte(0x7fffffffffffff80L), 0x80);
}

TEST(low_byte_of_negative_number) {
    EXPECT_EQ_INT(low_byte(-1), 255);
}

TEST(linear_preserves_registers) {
    EXPECT_PRESERVES(linear, (3, 4, 5));
}

TEST(low_byte_preserves_registers) {
    EXPECT_PRESERVES(low_byte, (0x1234));
}
