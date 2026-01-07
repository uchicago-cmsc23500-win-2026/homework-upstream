use solution::{hello, increase, is_leap_year, plus_one};

#[test]
fn check_hello() {
    assert_eq!(hello(), "Hello World!");
}

#[test]
fn check_leap_year1() {
    assert!(is_leap_year(2020));
}

#[test]
fn check_leap_year2() {
    assert_eq!(is_leap_year(1557), false);
}

#[test]
fn check_leap_year3() {
    assert_eq!(is_leap_year(1900), false);
}

#[test]
fn test_incr() {
    let mut n: i32 = 9;
    plus_one(&mut n);
    assert_eq!(n, 10);
}

#[test]
fn test_increase() {
    let mut n: i32 = 9;
    increase(&mut n, 3);
    assert_eq!(n, 12);
}
