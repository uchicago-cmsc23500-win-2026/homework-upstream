use module_4::task0::{get_boxed_thing, Thing};
use std::mem::size_of_val;

#[test]
fn test_box_thing() {
    let thing = Thing::new(2, 5);
    assert_eq!(thing.do_x(), 9);
    assert_eq!(size_of_val(&thing), 816);
    let box_thing = get_boxed_thing(thing);
    assert_eq!(size_of_val(&box_thing), 8);
    assert_eq!(box_thing.do_x(), 9);
}
