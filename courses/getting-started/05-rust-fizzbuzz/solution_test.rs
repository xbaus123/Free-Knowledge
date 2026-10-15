use super::*;

#[test]
fn plain_numbers() {
    assert_eq!(fizzbuzz(1), "1");
    assert_eq!(fizzbuzz(7), "7");
}

#[test]
fn fizz() {
    assert_eq!(fizzbuzz(9), "Fizz");
}

#[test]
fn buzz() {
    assert_eq!(fizzbuzz(10), "Buzz");
}

#[test]
fn fizzbuzz_for_15() {
    assert_eq!(fizzbuzz(15), "FizzBuzz");
}
