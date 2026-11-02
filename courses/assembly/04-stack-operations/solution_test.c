#include "fk_asm.h"

void reverse(long *xs, long n) ASM_FUNCTION(reverse);
long square(long x) ASM_FUNCTION(square);
long sum_of_squares(long a, long b) ASM_FUNCTION(sum_of_squares);

TEST(reverse_five_values) {
    long xs[] = {1, 2, 3, 4, 5};
    reverse(xs, 5);
    EXPECT_EQ_INT(xs[0], 5);
    EXPECT_EQ_INT(xs[1], 4);
    EXPECT_EQ_INT(xs[2], 3);
    EXPECT_EQ_INT(xs[3], 2);
    EXPECT_EQ_INT(xs[4], 1);
}

TEST(reverse_even_length) {
    long xs[] = {-8, 0, 42, 7};
    reverse(xs, 4);
    EXPECT_EQ_INT(xs[0], 7);
    EXPECT_EQ_INT(xs[1], 42);
    EXPECT_EQ_INT(xs[2], 0);
    EXPECT_EQ_INT(xs[3], -8);
}

TEST(reverse_only_touches_n_values) {
    long xs[] = {1, 2, 3, 99};
    reverse(xs, 3);
    EXPECT_EQ_INT(xs[0], 3);
    EXPECT_EQ_INT(xs[2], 1);
    EXPECT_EQ_INT(xs[3], 99);
}

TEST(reverse_empty) {
    long xs[] = {6};
    reverse(xs, 0);
    EXPECT_EQ_INT(xs[0], 6);
}

TEST(square_positive_and_negative) {
    EXPECT_EQ_INT(square(12), 144);
    EXPECT_EQ_INT(square(-5), 25);
}

TEST(sum_of_squares_small_numbers) {
    EXPECT_EQ_INT(sum_of_squares(3, 4), 25);
}

TEST(sum_of_squares_with_negatives) {
    EXPECT_EQ_INT(sum_of_squares(-6, 8), 100);
}

TEST(sum_of_squares_with_zero) {
    EXPECT_EQ_INT(sum_of_squares(0, 9), 81);
}

TEST(reverse_preserves_registers) {
    long xs[] = {1, 2, 3};
    EXPECT_PRESERVES(reverse, (xs, 3));
}

TEST(sum_of_squares_preserves_registers) {
    EXPECT_PRESERVES(sum_of_squares, (3, 4));
}
