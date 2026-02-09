use module_4::task1::compute_threaded_sum;

#[test]
fn test_threaded_sum_small() {
    let prices: Vec<f32> = (0..10).map(|i| i as f32).collect();
    let sequential_sum: f32 = prices.iter().sum();
    let threaded_sum = compute_threaded_sum(&prices, 2);

    println!(
        "Small test - Sequential: {:.2}, Threaded: {:.2}",
        sequential_sum, threaded_sum
    );
    assert!((threaded_sum - sequential_sum).abs() < f32::EPSILON);
}

#[test]
fn test_threaded_sum_medium() {
    let prices: Vec<f32> = (0..100).map(|i| (i as f32 * 0.5) + 5.0).collect();
    let sequential_sum: f32 = prices.iter().sum();
    let threaded_sum = compute_threaded_sum(&prices, 4);

    println!(
        "Medium test - Sequential: {:.2}, Threaded: {:.2}",
        sequential_sum, threaded_sum
    );
    assert!((threaded_sum - sequential_sum).abs() < f32::EPSILON);
}

#[test]
fn test_threaded_sum_large() {
    let prices: Vec<f32> = (0..10000).map(|i| (i as f32 * 0.1) + 1.5).collect();
    let sequential_sum: f32 = prices.iter().sum();
    let threaded_sum = compute_threaded_sum(&prices, 8);

    println!(
        "Large test - Sequential: {:.2}, Threaded: {:.2}",
        sequential_sum, threaded_sum
    );
    assert!((threaded_sum - sequential_sum).abs() < f32::EPSILON);
}
