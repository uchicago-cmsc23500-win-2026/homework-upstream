/*
 * Run both functions (using main.rs), one with standard mutexes and the other with RwLocks.
 * What differences do you observe in their behavior/output? Does this match
 * your understanding of how Read/Write locks work?
 *
 *  No submission is needed for this exercise.
 */

use std::sync::{Arc, Mutex, RwLock};
use std::thread;

pub fn read_write_locks() {
    let lock = Arc::new(RwLock::new(0));
    let mut handles = Vec::with_capacity(10);

    for _i in 0..10 {
        let c_lock = Arc::clone(&lock);
        let reader = thread::spawn(move || {
            for _j in 0..20 {
                let r = c_lock.read().unwrap();
                println!("RwLock: Read value as {}", *r);
            }
        });
        handles.push(reader)
    }

    for _j in 0..20 {
        let mut val = lock.write().unwrap();
        *val += 1;
        println!("RwLock: Incremented value by 1 to {}", *val);
    }

    for handle in handles {
        handle.join().unwrap();
    }
}

pub fn read_write_mutex() {
    let lock = Arc::new(Mutex::new(0));
    let mut handles = Vec::with_capacity(10);

    for _i in 0..10 {
        let reader_lock = lock.clone();
        let reader = thread::spawn(move || {
            for _j in 0..20 {
                let r = reader_lock.lock().unwrap();
                println!("Mutex: Read value as {}", *r);
            }
        });
        handles.push(reader)
    }

    for _j in 0..20 {
        let mut val = lock.lock().unwrap();
        *val += 1;
        println!("Mutex: Incremented value by 1 to {}", *val);
    }

    for handle in handles {
        handle.join().unwrap();
    }
}
