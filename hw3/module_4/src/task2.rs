use std::sync::{Arc, Mutex};
use std::thread;

struct Counter {
    count: i32,
}

fn incr(/* TODO: Insert Counter Struct Parameter here */) {
    // TODO: Complete this function, which should increment the counter
    // struct's count field in-place
}

pub fn mutex_counter_with_iterations(num_iterations: i32) -> i32 {
    // declare a counter wrapped in a mutex
    // spawn a thread to call incr() num_iterations times
    // in main thread call incr() num_iterations times
    // TODO: Initialize a counter variable, wrapped in a mutex here:
    let counter = /* TODO: Complete this assignment */


    let mut c = counter.clone();
    let handle = thread::spawn(move || {
        for _i in 0..num_iterations/2 {
            // TODO: Correctly call the increment function here
            /* Your call to incr() goes here */
            println!("thread spawned count {}", _i);
        }
    });

    // in the main thread, call incr() num_iterations times
    let mut c_main = counter.clone();
    for _i in 0..num_iterations/2 {
        // TODO: Correctly call the increment function here
        /* Your call to incr() goes here */
        println!("thread main count {}", _i);
    }

    handle.join().unwrap();

    let final_count = counter.lock().unwrap().count;

    // If done correctly, the counter should be incremented
    // exactly num_iterations
    println!("Final Counter Value {}", final_count);
    final_count
}

pub fn get_counter_for_test(num_iterations: i32) -> i32 {
    mutex_counter_with_iterations(num_iterations)
}
