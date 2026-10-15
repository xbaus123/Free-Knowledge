#include "fk_test.h"

int max_of(const int *xs, int n);

TEST(finds_max_in_middle) {
    int xs[] = {3, 9, 2};
    EXPECT_EQ_INT(max_of(xs, 3), 9);
}

TEST(single_element) {
    int xs[] = {42};
    EXPECT_EQ_INT(max_of(xs, 1), 42);
}

TEST(all_negative) {
    int xs[] = {-5, -2, -9};
    EXPECT_EQ_INT(max_of(xs, 3), -2);
}
