pub struct Animal<T>
where
    T: AnimalBehavior,
{
    pub name: String,
    pub animal_type: T,
    pub weight: u8,
}

pub trait AnimalBehavior {
    fn make_sound(&self) -> &str;
}

pub struct Dog {
    pub breed: String,
}

pub struct Parrot {
    pub color: String,
}

impl AnimalBehavior for Dog {
    panic!("TODO: Complete this Code Segment");
}

impl AnimalBehavior for Parrot {
    panic!("TODO: Complete this Code Segment");
}
