use rand::Rng;
use std::collections::HashMap;
use std::fs::File;
use std::io::Error;
use std::io::{BufReader, BufWriter, Read, Write};

use module_3::basic::{deserialize_from_bytes, serialize_to_bytes, serialize_to_string};
use module_3::hashmap::{deserialize_data_from_disk, serialize_data_to_disk};
use module_3::structure::{
    University, deserialize_jsonstring_to_struct, deserialize_struct_from_cbor,
    serialize_struct_to_cbor, serialize_struct_to_jsonstring,
};
use module_3::vector::{deserialize_vector_from_disk, serialize_vector_to_disk};

fn write_bytes_to_file(bytes: [u8; 4], filename: &str) -> Result<(), Error> {
    // Create a File; see Rust doc for std::fs::File
    let mut buffer = File::create(filename)?;
    // Write bytes to that file
    buffer.write_all(&bytes)?;
    Ok(())
}

fn read_bytes_from_file(filename: &str) -> [u8; 4] {
    let f = File::open(filename).expect("could not open file");
    let mut reader = BufReader::new(f);
    let mut buffer = Vec::new();

    // Read file into vector.
    reader
        .read_to_end(&mut buffer)
        .expect("error while reading file");

    // Transform Vec (much preferred way of handling collection of values) into array (for this example)
    let array = vec_to_array(buffer);
    array
}

fn write_string_to_file(string: &str, filename: &str) {
    let f = File::create(filename).expect("error creating file");
    let mut f = BufWriter::new(f);
    f.write_all(string.as_bytes()).unwrap();
}

fn read_string_from_file(filename: &str) -> String {
    let mut data = String::new();
    let f = File::open(filename).expect("error while opening file");
    let mut br = BufReader::new(f);
    br.read_to_string(&mut data).unwrap();
    data
}

fn vec_to_array<T, const N: usize>(v: Vec<T>) -> [T; N] {
    v.try_into()
        .unwrap_or_else(|v: Vec<T>| panic!("Expected a Vec of length {} but it was {}", N, v.len()))
}

fn basic_serialization() {
    println!("Basic Integer serialization, deserialization");
    // Change this variable to serialize data (true) or deserialize it (false)
    let serialize = true;
    let bytes_filename = "test.bytes";
    let string_filename = "test.txt";
    let integer: u32 = 33;
    if serialize {
        // We obtain a human-readable representation of the data (integer) to store
        let integer_in_string = serialize_to_string(integer);
        // Then we store the string into a file
        write_string_to_file(&integer_in_string, &string_filename);

        // We obtain a byte representation of the data (integer) to store
        let integer_in_bytes = serialize_to_bytes(integer);
        // Then we store the byte representation on a file on disk
        write_bytes_to_file(integer_in_bytes, &bytes_filename).unwrap();
    } else {
        // We read string from file (we can deserialize it directly into a rust string)
        let data = read_string_from_file(&string_filename);
        println!("The (string) deserialized integer is: {}", data);

        // We read bytes from a file
        let read_bytes = read_bytes_from_file(&bytes_filename);
        let deserialized_integer = deserialize_from_bytes(read_bytes);
        println!(
            "The (bytes) deserialized integer is: {}",
            deserialized_integer
        );
    }
}

fn vector_serialization() {
    println!("Serializing and Deserializing vectors");
    // Change this variable to serialize data (true) or deserialize it (false)
    let serialize = true;
    let filename = "data.bin";

    if serialize {
        let mut rng = rand::thread_rng();
        let n1: u32 = rng.gen_range(1500..10000);
        let mut counter = 0;
        let mut data = Vec::new();

        for _i in 1000..n1 {
            data.push(counter);
            counter += 1;
        }
        serialize_vector_to_disk(data, &filename).unwrap();
    } else {
        let data = deserialize_vector_from_disk(&filename);
        println!("The size of the array is: {}", data.len());
        println!("This is the data:");
        for i in data.iter() {
            println!("Element: {}", i);
        }
        println!("The size of the array is (again): {}", data.len());
    }
}

fn hashmap_serialization() {
    println!("Serializing and Deserializing hashmaps");
    // Change this variable to serialize data (true) or deserialize it (false)
    let serialize = true;
    let filename = "data.bin";
    let data: HashMap<String, i32> = HashMap::from([
        ("Mercury".to_string(), 4),
        ("Venus".to_string(), 7),
        ("Earth".to_string(), 0),
        ("Mars".to_string(), 5),
    ]);
    if serialize {
        serialize_data_to_disk(data, &filename).unwrap();
    } else {
        let deserialized_data = deserialize_data_from_disk(&filename);
        println!("The size of the hashmap is: {}", deserialized_data.len());
        println!("This is the data:");
        for (key, value) in &deserialized_data {
            println!("{}: {}", key, value);
        }
        assert_eq!(data == deserialized_data, true);
    }
}

fn structure_serialization() {
    let json_string = r#"
        {
            "name": "University of Chicago",
            "undergraduate_enrollment": 7559,
            "graduate_enrollment": 10893,
            "schools": [
                "Biological Sciences Division",
                "Chicago Booth School of Business",
                "Crown Family School of Social Work, Policy, and Practice",
                "Divinity School",
                "Graham School of Continuing Liberal and Professional Studies",
                "Harris School of Public Policy",
                "Humanities Division",
                "Law School",
                "Physical Sciences Division",
                "Pritzker School of Medicine",
                "Pritzker School of Molecular Engineering",
                "Social Sciences Division"
            ],
            "acceptance_rate": 0.07
        }"#;

    // convert json to struct
    let uchicago: University = deserialize_jsonstring_to_struct(json_string);
    println!("{:?}", uchicago);

    // convert struct to json
    let serialized = serialize_struct_to_jsonstring(&uchicago);
    println!("serialized = {}", serialized);

    let filename = "uchicago.cbor";

    serialize_struct_to_cbor(&uchicago, filename);

    let uchicago_from_cbor: University = deserialize_struct_from_cbor(filename);
    println!("{:?}", uchicago_from_cbor);
}

fn main() {
    // Uncomment each function call to run the main code for each part
    //basic_serialization();
    //vector_serialization();
    //hashmap_serialization();
    //structure_serialization();
}
