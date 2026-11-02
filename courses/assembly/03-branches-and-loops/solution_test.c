#include "fk_asm.h"

long max2(long a, long b) ASM_FUNCTION(max2);
long sum_array(const long *xs, long n) ASM_FUNCTION(sum_array);

TEST(max2_first_is_larger) {
    EXPECT_EQ_INT(max2(9, 4), 9);
}

TEST(max2_second_is_larger) {
    EXPECT_EQ_INT(max2(4, 9), 9);
}

TEST(max2_negative_numbers) {
    EXPECT_EQ_INT(max2(-7, -3), -3);
}

TEST(max2_compares_signed) {
    EXPECT_EQ_INT(max2(-1, 1), 1);
}

TEST(sum_array_several_values) {
    long xs[] = {1, 2, 3, 4, 5};
    EXPECT_EQ_INT(sum_array(xs, 5), 15);
}

TEST(sum_array_with_negatives) {
    long xs[] = {10, -4, 7, -20};
    EXPECT_EQ_INT(sum_array(xs, 4), -7);
}

TEST(sum_array_only_reads_n_values) {
    long xs[] = {1, 2, 3, 1000};
    EXPECT_EQ_INT(sum_array(xs, 3), 6);
}

TEST(sum_array_empty) {
    long xs[] = {99};
    EXPECT_EQ_INT(sum_array(xs, 0), 0);
}

TEST(max2_preserves_registers) {
    EXPECT_PRESERVES(max2, (4, 9));
}

TEST(sum_array_preserves_registers) {
    long xs[] = {1, 2, 3};
    EXPECT_PRESERVES(sum_array, (xs, 3));
}
