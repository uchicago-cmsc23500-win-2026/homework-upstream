use module_3::hashmap::{deserialize_data_from_disk, serialize_data_to_disk};
use rand::{Rng, distributions::Alphanumeric};
use std::collections::HashMap;

#[test]
fn test_serialize_deserialize_data_to_disk() {
    let n: i32 = generate_rand_num(1000, 2000);
    let filename = "hashmap_test.bin";
    let mut test_map: HashMap<String, i32> = HashMap::new();

    for _i in 0..n {
        let key = generate_rand_string();
        let value = generate_rand_num(1000, 20000);
        test_map.insert(key, value);
    }

    serialize_data_to_disk(test_map.clone(), &filename).unwrap();
    let return_map = deserialize_data_from_disk(&filename);

    assert_eq!(return_map == test_map, true);
}

fn generate_rand_string() -> String {
    let mut rng = rand::thread_rng();
    let str_len: usize = rng.gen_range(10..100);
    let s: String = rand::thread_rng()
        .sample_iter(&Alphanumeric)
        .take(str_len)
        .map(char::from)
        .collect();
    s
}

fn generate_rand_num(min: i32, max: i32) -> i32 {
    let mut rng = rand::thread_rng();
    let num: i32 = rng.gen_range(min..max);
    num
}
