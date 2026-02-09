use std::sync::Arc;
use std::thread;

pub fn compute_threaded_sum(prices: &[f32], num_threads: usize) -> f32 {
    let num_prices = prices.len();
    let chunk_size = num_prices / num_threads;

    //TODO: Make prices shareable across threads
    let p = // ??? ;

    let mut handles = Vec::new();
    let mut partial_sums = Vec::new();

    for i in 0..num_threads {
        let start = i * chunk_size;
        let end = start + chunk_size;

        //TODO: Clone your shared prices for this thread
        let thread_prices = //??? ;

        let handle = thread::spawn(move || {
            let chunk = &thread_prices[start..end];

            //TODO: Compute the partial sum from the chunk
            let partial_sum: f32 = //??? ;
            
            //TODO: Return the value here (the sum for this thread)
            return //????;
        });
        handles.push(handle);
    }

    // Collect partial sums from threads
    for handle in handles {
        let partial_sum = handle.join().unwrap();
        partial_sums.push(partial_sum);
    }

    // Compute the total sum from partial sums
    partial_sums.iter().sum()
}

pub fn threaded_sum() {
    let prices: Vec<f32> = (0..100).map(|i| (i as f32 * 0.5) + 5.0).collect();
    let num_prices = prices.len();
    const NUM_THREADS: usize = 4;

    println!("Calculating sum of {num_prices} prices using {NUM_THREADS} threads.");

    let total_sum = compute_threaded_sum(&prices, NUM_THREADS);

    // Compute the sequential sum
    let sequential_sum: f32 = prices.iter().sum();

    println!("Total sum (parallel): {:.2}", total_sum);
    println!("Total sum (sequential): {:.2}", sequential_sum);

    // Compare the results
    if (total_sum - sequential_sum).abs() < f32::EPSILON {
        println!("The sums match!");
    } else {
        println!("The sums do not match!");
    }

    println!("All threads finished.");
}
