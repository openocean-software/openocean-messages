# openocean-messages
Generic messages for ocean system and tools to generate native formats

Messages are defined in Protobuf. Every numeric field declares its units as a [UDUNITS-2](https://docs.unidata.ucar.edu/udunits/current/) string using the `(openocean.field).units` option.

## Repo Structure

- src: Source code
  - openocean/messages: Message definitions (Protobuf, imported as `openocean/messages/*.proto`)
    - options.proto: Field options (units)
    - common.proto: Types shared between messages (Speed, Euler)
    - navigation.proto: Navigation (vehicle state)
    - control.proto: ControlSetpoint (heading, speed, depth, etc.)
    - nanopb.options: nanopb size limits
  - generators: protoc plugins that generate other formats
    - protoc-gen-ros: ROS 2 interface package
    - protoc-gen-lcm: LCM types and C++ converters
  - test: Checks that all units parse with UDUNITS-2 and that fields ControlSetpoint shares with Navigation have the same type and units, and tests for each output
- rust: Rust crate (`build.rs` generates the types with prost)

## Conventions

- Geodetic position is latitude, longitude, and depth (positive down)
- Local position is ENU e, n, u about a datum (u = -depth)
- Body-frame velocities are forward, starboard, down (Fossen / SNAME)
- Heading and course are clockwise from true north
- Unset optional fields are unknown (Navigation) or not controlled (ControlSetpoint)

## Building

Install the dependencies (Ubuntu) for the outputs you want, then build with CMake and Ninja:

```
./init.sh --cxx --python --ros --nanopb --rust --lcm
./build.sh
ctest --test-dir build
```

`build.sh` passes any arguments on to CMake, and `BUILD_DIR` overrides the build directory (default `build`).

### Outputs

| `init.sh` | CMake option | Default | Output |
|---|---|---|---|
| `--cxx` | `OPENOCEAN_CPP` | ON | `openocean_messages` library (`#include "openocean/messages/navigation.pb.h"`) |
| `--python` | `OPENOCEAN_PYTHON` | OFF | `build/python` (`from openocean.messages import navigation_pb2`) |
| `--ros` | `OPENOCEAN_ROS` | OFF | `build/ros/openocean_msgs` and `build/ros/openocean_msgs_convert` ROS 2 package sources, to build with colcon |
| `--nanopb` | `OPENOCEAN_NANOPB` | OFF | `openocean_messages_nanopb` C library (`#include "openocean/messages/navigation.pb.h"`, from `build/nanopb`) |
| `--rust` | `OPENOCEAN_RUST` | OFF | `openocean-messages` crate in `rust/` (prost), built into `build/rust` |
| `--lcm` | `OPENOCEAN_LCM` | OFF | `openocean_messages_lcm` LCM types (`#include "openocean/navigation_t.hpp"`); with `--cxx`, also `openocean_messages_lcm_convert` (`#include "openocean/lcm_convert.h"`) |

`init.sh` with no options is `--cxx`. It writes `init.cmake`, which sets the option defaults for new build directories to the outputs it installed; `-D` still overrides them.

For example, with ROS 2 sourced:

```
./init.sh --ros
./build.sh
colcon build --base-paths build/ros
```

### nanopb

`src/openocean/messages/nanopb.options` limits each repeated and string field (e.g. at most 2 `Navigation.speed` entries, 32-character strings), so every field is a fixed-size struct member rather than a callback. Messages that exceed a limit fail to encode or decode with nanopb.

### Rust

`rust/` is a Cargo crate whose `build.rs` generates the types with [prost](https://github.com/tokio-rs/prost) from `src/openocean/messages`. It can also be built with cargo directly (`cargo build` in `rust/`, with `protoc` on the `PATH`), or used from another crate as a path dependency. `rust-version` is 1.75 (Ubuntu 24.04's cargo), and `Cargo.lock` pins dependencies that build with it.

### Protobuf to LCM

`protoc-gen-lcm` writes one `.lcm` type per message and enum (package `openocean`, e.g. `navigation_t`, `navigation_geodetic_t`), and `lcm-gen` their C++ types. With `OPENOCEAN_CPP`, it also writes `openocean/lcm_convert.h`, with `to_lcm()` and `from_lcm()` overloads for each message.

| Protobuf | LCM |
|---|---|
| `optional` field, or singular message field | `boolean has_<field>` before the field |
| nested message or enum | flattened: `Navigation.Geodetic` → `navigation_geodetic_t` |
| enum | struct with the values as `const int32_t` (common prefix removed) and an `int32_t value` |
| `oneof` | its fields, plus `int32_t <oneof>_case` and constants holding the field numbers |
| `repeated`, `map` | `int32_t num_<field>` and a variable-length array (map entries sorted by key) |
| `bytes` | `int32_t num_<field>` and `byte[]` |
| `uint32`, `uint64` | `int64_t` (the converter throws for a `uint64` above `INT64_MAX`) |
| `google.protobuf.Timestamp`, `Duration` | `int64_t` microseconds |

### Protobuf to ROS 2

`protoc-gen-ros` writes two packages: `openocean_msgs`, with the messages, and `openocean_msgs_convert`, which builds the Protobuf C++ library and provides `to_ros()` and `from_ros()` overloads for each message (`#include <openocean_msgs_convert/convert.hpp>`, target `openocean_msgs_convert::openocean_msgs_convert`).

| Protobuf | ROS 2 |
|---|---|
| `optional` field, or singular message field | `bool has_<field>` before the field |
| nested message or enum | flattened: `Navigation.Geodetic` → `NavigationGeodetic` |
| enum | message with the values as constants (common prefix removed) and a `value` field |
| `oneof` | its fields, plus `<oneof>_case` and constants holding the field numbers |
| `repeated` | unbounded array |
| `bytes` | `uint8[]` |
| units `<s, ms, us, ns> since 1970-01-01 00:00:00 UTC`, `google.protobuf.Timestamp` | `builtin_interfaces/Time` |
| `google.protobuf.Duration` | `builtin_interfaces/Duration` |
| units | trailing `# [units]` comment |

Field names that are Python or C++ keywords are rejected.

`src/test/expected` holds what the ROS 2 and LCM generators should produce from `src/test/mapping.proto`; after an intended change to a generator, run `ninja -C build update_expected` and review the diff.

## License

Apache-2.0; see [LICENSE](LICENSE).
