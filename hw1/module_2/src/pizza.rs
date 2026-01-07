/*
Result and Option

- Create a Pizza struct that has a vector of Toppings
*/

#[derive(Clone, Copy, PartialEq)]
pub enum Toppings {
    Onion,
    Sausage,
    Pineapple,
    Spinach,
    Cheetos,
    Oreos,
}

pub struct Pizza {
    toppings: Vec<Toppings>,
}

impl Pizza {
    /// Create a new empty pizza
    pub fn new() -> Self {
        panic!("TODO: Complete this Code Segment");
    }

    /// Add this topping to the pizza
    /// Return/throw a PizzaError if the topping is not valid according to check_topping
    pub fn add_topping(&mut self, topping: Toppings) -> Result<(), PizzaError> {
        panic!("TODO: Complete this Code Segment");
    }

    /// See if this pizza has a topping and how many times it was added.
    /// Return none if it was never added
    pub fn has_topping(&self, topping: &Toppings) -> Option<usize> {
        panic!("TODO: Complete this Code Segment");
    }
}

/// A simple empty struct to indicate an error. This could be an enum and could hold data.
#[derive(Debug, Clone)]
pub struct PizzaError;

/// Check if a topping is valid. Returns a Result of an Ok() or PizzaError if not
pub fn check_topping(topping: &Toppings) -> Result<(), PizzaError> {
    match topping {
        Toppings::Onion => Ok(()),
        Toppings::Pineapple => Ok(()),
        Toppings::Spinach => Ok(()),
        Toppings::Sausage => Ok(()),
        _ => Err(PizzaError {}),
    }
}
