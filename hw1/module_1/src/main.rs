use solution::{hello, increase, is_leap_year, plus_one};

fn main() {
    println!("{}", hello());
    println!("Is 1900 a leap year? {}", is_leap_year(1900));
    println!("Is 2020 a leap year? {}", is_leap_year(2020));

    let mut n: i32 = 9;
    println!("n = {}", n);
    plus_one(&mut n);
    println!("plus_one(9) = {}", n);

    let mut n: i32 = 9;
    println!("n = {}", n);
    increase(&mut n, 3);
    println!("increase(9, 3) = {}", n);
}
