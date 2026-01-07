//use solution::{plus_one, Rectangle, Coin, coin_value};
use module_2::animal::*;
use module_2::coin::*;
use module_2::pizza::*;
use module_2::rectangle::*;

#[test]
fn test_rect_struct() {
    let r = Rectangle {
        width: 50,
        height: 25,
    };
    assert_ne!(r.is_square(), true);
}

#[test]
fn test_square_struct() {
    let r = Rectangle {
        width: 25,
        height: 25,
    };
    assert_eq!(r.is_square(), true);
}

#[test]
fn test_area_struct() {
    let r = Rectangle {
        width: 4,
        height: 8,
    };
    assert_eq!(r.calc_area(), 32);
}

#[test]
fn test_coins() {
    assert_eq!(coin_value(Coin::Nickel), 5);
    assert_eq!(coin_value(Coin::Dime), 10);
    assert_eq!(coin_value(Coin::Quarter), 25);
    assert_eq!(coin_value(Coin::Penny), 1);
}

#[test]
#[should_panic]
fn unwrap_bad_topping() {
    check_topping(&Toppings::Cheetos).unwrap();
}

#[test]
fn test_check_topping() {
    let sausage_ok = check_topping(&Toppings::Sausage).is_ok();
    let spinach_ok = check_topping(&Toppings::Spinach).is_ok();
    let cheetos_err = check_topping(&Toppings::Cheetos).is_err();
    assert!(sausage_ok);
    assert!(spinach_ok);
    assert!(cheetos_err);
}

#[test]
fn test_add_good_toppings() {
    let mut za = Pizza::new();
    let sausage_ok = za.add_topping(Toppings::Sausage).is_ok();
    let spinach_ok = za.add_topping(Toppings::Spinach).is_ok();
    let cheetos_err = za.add_topping(Toppings::Cheetos).is_err();
    assert!(sausage_ok);
    assert!(spinach_ok);
    assert!(cheetos_err);
}

#[test]
fn test_has_topping() {
    let mut za = Pizza::new();
    assert!(za.add_topping(Toppings::Sausage).is_ok());
    assert!(za.add_topping(Toppings::Sausage).is_ok());
    //FIXME This passes but is bad form... Can you fix it?
    assert_eq!(2, za.has_topping(&Toppings::Sausage).unwrap());
    //FIXME, this does not use the interface correctly
    assert_eq!(0, za.has_topping(&Toppings::Spinach).unwrap());
}

#[test]
fn test_generics_dog() {
    let dog = Animal {
        name: String::from("Lassie"),
        animal_type: Dog {
            breed: String::from("Collie"),
        },
        weight: 10,
    };

    assert_eq!(dog.animal_type.make_sound(), "Woof!");
}

#[test]
fn test_generics_bird() {
    let parrot = Animal {
        name: String::from("Polly"),
        animal_type: Parrot {
            color: String::from("Green"),
        },
        weight: 10,
    };

    assert_eq!(parrot.animal_type.make_sound(), "Polly wants a cracker!");
}
