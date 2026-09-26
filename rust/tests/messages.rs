//! Checks the prost types: proto3 presence as Option, repeated fields as Vec, and
//! wire compatibility with the other outputs.

use openocean_messages::{navigation, Navigation, Speed, SpeedMode};
use prost::Message;

fn example() -> Navigation {
    Navigation {
        time: 1_000_000,
        vehicle: Some(navigation::VehicleMetadata { name: "auv1".into() }),
        geodetic: Some(navigation::Geodetic {
            latitude: Some(41.5),
            depth: Some(10.0),
            ..Default::default()
        }),
        speed: vec![Speed {
            value: Some(1.5),
            mode: Some(SpeedMode::OverGround as i32),
        }],
        ..Default::default()
    }
}

#[test]
fn round_trip() {
    let nav = example();
    let decoded = Navigation::decode(nav.encode_to_vec().as_slice()).unwrap();
    assert_eq!(decoded, nav);
    assert!(decoded.enu.is_none());
    assert!(decoded.geodetic.unwrap().longitude.is_none());
}

/// The same Navigation encoded by the Python Protobuf output (protoc --python_out),
/// so a change in the Rust encoding shows up here.
const PYTHON_ENCODED: &[u8] = &[
    0x08, 0xc0, 0x84, 0x3d, 0x12, 0x06, 0x0a, 0x04, 0x61, 0x75, 0x76, 0x31, 0x52, 0x12, 0x09,
    0x00, 0x00, 0x00, 0x00, 0x00, 0xc0, 0x44, 0x40, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x24, 0x40, 0x6a, 0x0b, 0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf8, 0x3f, 0x10, 0x01,
];

#[test]
fn matches_protobuf_python() {
    assert_eq!(Navigation::decode(PYTHON_ENCODED).unwrap(), example());
    assert_eq!(example().encode_to_vec(), PYTHON_ENCODED);
}
