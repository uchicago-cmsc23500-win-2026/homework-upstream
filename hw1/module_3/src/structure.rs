use serde::{Deserialize, Serialize};
use std::fs::File;

#[derive(Debug, Serialize, Deserialize)]
pub struct University {
    pub name: String,
    pub undergraduate_enrollment: u16,
    pub graduate_enrollment: u16,
    pub schools: Vec<String>,
    pub acceptance_rate: f32,
}

pub fn serialize_struct_to_jsonstring(struct_data: &University) -> String {
    panic!("TODO: Complete this Code Segment");
}

pub fn deserialize_jsonstring_to_struct(string_data: &str) -> University {
    panic!("TODO: Complete this Code Segment");
}

pub fn serialize_struct_to_cbor(struct_data: &University, filename: &str) {
    panic!("TODO: Complete this Code Segment");
}

pub fn deserialize_struct_from_cbor(filename: &str) -> University {
    panic!("TODO: Complete this Code Segment");
}
