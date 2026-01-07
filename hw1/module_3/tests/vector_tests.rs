use module_3::vector::{deserialize_vector_from_disk, serialize_vector_to_disk};

#[test]
fn test_serialize_deserialize_vector_to_disk() {
    let n1: u32 = 100000;
    let mut counter = 0;
    let mut data = Vec::new();
    let filename = "vector_test.bin";

    for _i in 0..n1 {
        data.push(counter);
        counter += 1;
    }
    serialize_vector_to_disk(data, &filename).unwrap();

    let data = deserialize_vector_from_disk(&filename);

    assert_eq!(n1 as usize, data.len());
}
