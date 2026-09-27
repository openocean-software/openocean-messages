# Development

*This page was written by Claude.*

## Repository layout

- src: Source code
    - openocean/messages: Message definitions (Protobuf, imported as `openocean/messages/*.proto`)
        - options.proto: Field options (units)
        - common.proto: Types shared between messages (Speed, Euler, CustomValue)
        - navigation.proto: Navigation (vehicle state)
        - control.proto: ControlSetpoint (heading, speed, depth, etc.)
        - nanopb.options: nanopb size limits
    - generators: protoc plugins that generate other formats
        - protoc-gen-ros: ROS 2 interface package
        - protoc-gen-lcm: LCM types and C++ converters
        - ProtobufGenerateRos.cmake, ProtobufGenerateLcm.cmake: CMake functions that run them
    - test: Checks that all units parse with UDUNITS-2 and that fields ControlSetpoint shares with Navigation have the same type and units, and tests for each output
        - downstream: A project that uses openocean_messages with `find_package()`, from the build directory and from an installation
    - doc: This documentation ([mkdocs](https://www.mkdocs.org/))
- cmake: CMake package configuration
- rust: Rust crate (`build.rs` generates the types with prost)
- versions.env: Versions of the tools init.sh and CI download
- mkdocs.yml: Configuration for this documentation

## Tests

`ctest --test-dir build` runs the tests for the enabled outputs.

`src/test/expected` holds what the ROS 2 and LCM generators should produce from `src/test/mapping.proto`; after an intended change to a generator, run `ninja -C build update_expected` and review the diff.

## Pinned versions

`versions.env` holds the versions of the tools that `init.sh` and CI download (buf, ros2-apt-source) and the ROS 2 distribution for each Ubuntu release. Rust dependencies are pinned by `rust/Cargo.lock`, and the rest come from Ubuntu's packages.

## Documentation

With `mkdocs` and `mkdocs-material` installed (e.g. `apt install mkdocs mkdocs-material`), `mkdocs serve` previews these pages, and `mkdocs build --strict` builds them into `site/` as CI does.
