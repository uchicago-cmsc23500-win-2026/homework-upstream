use module_4::task1::threaded_sum;
use module_4::task2::mutex_counter;
use module_4::task3::{read_write_locks, read_write_mutex};

fn main() {
    // Run each of these functions to test the various tasks.
    threaded_sum();
    mutex_counter();
    read_write_locks();
    read_write_mutex();
}
