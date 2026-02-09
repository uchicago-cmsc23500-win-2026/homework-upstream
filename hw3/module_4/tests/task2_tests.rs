use module_4::task2::get_counter_for_test;

#[test]
fn test_mutex_counter_small() {
    let num_iterations = 10;
    let final_count = get_counter_for_test(num_iterations);
    println!(
        "Small test (10 iterations each): Final count = {}",
        final_count
    );
    assert_eq!(final_count, num_iterations * 2);
}

#[test]
fn test_mutex_counter_medium() {
    let num_iterations = 100;
    let final_count = get_counter_for_test(num_iterations);
    println!(
        "Medium test (100 iterations each): Final count = {}",
        final_count
    );
    assert_eq!(final_count, num_iterations * 2);
}

#[test]
fn test_mutex_counter_large() {
    let num_iterations = 1000;
    let final_count = get_counter_for_test(num_iterations);
    println!(
        "Large test (1000 iterations each): Final count = {}",
        final_count
    );
    assert_eq!(final_count, num_iterations * 2);
}

#[test]
fn test_mutex_counter_function() {
    let num_iterations = 25;
    let final_count = get_counter_for_test(num_iterations);
    assert_eq!(final_count, num_iterations * 2);
}
