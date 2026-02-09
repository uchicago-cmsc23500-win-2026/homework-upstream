pub struct Thing {
    pub i: usize,
    pub j: [usize; 100],
    pub k: usize,
}

impl Thing {
    pub fn new(i: usize, k: usize) -> Self {
        Thing {
            i,
            j: [i; 100],
            k,
        }
    }

    pub fn do_x(&self) -> usize {
        self.i + self.k + self.j[1]
    }
}

pub fn get_boxed_thing(thing: Thing) -> Box<Thing> {
    // TODO replace this to create a Box<Thing> from thing
    panic!("TODO");
}
