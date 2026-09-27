# Rust

*This page was written by Claude.*

`rust/` is a Cargo crate whose `build.rs` generates the types with [prost](https://github.com/tokio-rs/prost) from `src/openocean/messages`. It can also be built with cargo directly (`cargo build` in `rust/`, with `protoc` on the `PATH`), or used from another crate as a path dependency. `rust-version` is 1.75 (Ubuntu 24.04's cargo), and `Cargo.lock` pins dependencies that build with it.
