# openocean-messages

This project aims to provide a subset of common messages to improve interoperability between marine robotic systems, *regardless of middleware or programming language.*

In this repo are generic messages (defined in Protobuf) for ocean systems and tools to generate native formats from these messages. 

Messages are automatically converted to the desired output format as a first-class native type, so Protobuf is *not needed at runtime* for non-Protobuf output types (e.g. ROS Msg).

The output formats currently supported by this project are:

- Protobuf
  - C++ (built-in)
  - Python (built-in)
  - Rust (prost)
  - C (nanopb)
* ROS2 Msg
	- Conversion to/from Protobuf optional.
* LCM types
	- Conversion to/from Protobuf optional.

This project is an initiative of Open Ocean Software: https://oceansoft.org.

## Repo Structure

*This section was written by Claude.*

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
- cmake: CMake package configuration
- rust: Rust crate (`build.rs` generates the types with prost)

## Conventions

*This section was written by Claude.*

- Geodetic position is latitude, longitude, and depth (positive down)
- Local position is ENU: **e**ast, **n**orth, **u**p about a datum (where up = -depth), relative to some datum (in latitude/longitude).
- Body-frame velocities are forward, starboard, down (Fossen / SNAME)
- Heading and course are clockwise from true north.
- Optional fields indicate no data (Navigation) or not controlled (ControlSetpoint).

## Extending the messages

*This section was written by Claude.*

Projects that need more than openocean's fields should wrap the openocean message in their own (composition):

```protobuf
import "openocean/messages/navigation.proto";

message ContactReport
{
    openocean.Navigation nav = 1;
    string type = 2;
    optional double length = 3;
}
```

Composition works with every output: the ROS 2 and LCM generators refer to openocean's types with `dep=` (see [Using from another project](#using-from-another-project)), so the wrapper is a native, typed message there too. It is a different message from `openocean.Navigation`, though, so subscribers to that type don't see it.

For a few loosely typed values (e.g. one more sensor reading), `Navigation.custom` and `ControlSetpoint.custom` hold a list of `CustomValue` (name, value, and UDUNITS-2 units) instead.

Field numbers 1000 and up are reserved in `Navigation` and `ControlSetpoint`, for messages that repeat their fields and add their own, so Protobuf readers of the openocean message can still read them.

Fields several projects need belong in openocean itself.

## Building

*This section was written by Claude.*

Install the dependencies (Ubuntu) for the outputs you want, then build with CMake and Ninja:

```
./init.sh --cxx --python --ros --nanopb --rust --lcm
./build.sh
ctest --test-dir build
```

`build.sh` passes any arguments on to CMake, and `BUILD_DIR` overrides the build directory (default `build`).

### Outputs

*This section was written by Claude.*

| `init.sh` | CMake option (Boolean)  | Output |
|---|---|---|
| `--cxx` | `OPENOCEAN_CPP`  | `openocean_messages` library (`#include "openocean/messages/navigation.pb.h"`) |
| `--python` | `OPENOCEAN_PYTHON`  | `build/python` (`from openocean.messages import navigation_pb2`) |
| `--ros` | `OPENOCEAN_ROS`  | `build/ros/openocean_msgs` and `build/ros/openocean_msgs_convert` ROS 2 package sources, to build with colcon |
| `--nanopb` | `OPENOCEAN_NANOPB`  | `openocean_messages_nanopb` C library (`#include "openocean/messages/navigation.pb.h"`, from `build/nanopb`) |
| `--rust` | `OPENOCEAN_RUST`  | `openocean-messages` crate in `rust/` (prost), built into `build/rust` |
| `--lcm` | `OPENOCEAN_LCM`  | `openocean_messages_lcm` LCM types (`#include "openocean/navigation_t.hpp"`); *with* `--cxx`, also `openocean_messages_lcm_convert` (`#include "openocean/lcm_convert.h"`) |

Libraries build shared by default (`-DBUILD_SHARED_LIBS=OFF` builds them static), as do the generated ROS 2 converter packages. The version (`project(VERSION)` in `CMakeLists.txt`) carries through to the libraries, the ROS 2 packages, and the Rust crate (checked by the `version_consistent` test). `OPENOCEAN_SOVERSION` is the shared libraries' ABI version.

`init.sh` with no options is `--cxx`. It writes `init.cmake`, which sets the option defaults for new build directories to the outputs it installed; `-D` still overrides them.

For example, with ROS 2 sourced:

```
./init.sh --ros
./build.sh
colcon build --base-paths build/ros
```

### Installing

*This section was written by Claude.*

`cmake --install build` (with `--prefix` and `DESTDIR` as usual) installs the enabled outputs:

| Output | Installed to |
|---|---|
| Protos | `include/openocean/messages` (also the import directory) |
| C++ | `lib/libopenocean_messages.so.1`, headers in `include/openocean/messages` |
| nanopb | `lib/libopenocean_messages_nanopb.so.1`, headers in `include/openocean_messages_nanopb/openocean/messages` |
| LCM | C++ types and `lcm_convert.h` in `include/openocean`, `.lcm` types in `share/openocean_messages/lcm` |
| Python | `lib/python3/dist-packages` (`OPENOCEAN_INSTALL_PYTHON_DIR`) |
| Generators | `share/openocean_messages/generators` |
| CMake package | `lib/cmake/openocean_messages` (`share/cmake/openocean_messages` without the C++ or nanopb libraries) |

Paths follow GNUInstallDirs, so with `CMAKE_INSTALL_PREFIX=/usr` (as `dh_auto_configure` sets) libraries go in the multiarch directory, e.g. `lib/x86_64-linux-gnu`. Nothing gets an RPATH. The ROS 2 packages are installed with colcon, and the Rust crate is used with cargo.

### Using from another project

*This section was written by Claude.*


```cmake
find_package(openocean_messages 0.1 REQUIRED COMPONENTS cpp)
add_library(my_messages)
protobuf_generate(TARGET my_messages LANGUAGE cpp PROTOS my/messages/vehicle.proto
  IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR} ${openocean_messages_PROTO_DIR}
  PROTOC_OUT_DIR ${CMAKE_CURRENT_BINARY_DIR})
target_include_directories(my_messages PUBLIC ${CMAKE_CURRENT_BINARY_DIR})
target_link_libraries(my_messages PUBLIC openocean_messages::openocean_messages)
```

Link openocean's library rather than compiling its protos again, which Protobuf rejects when both end up in one process.

| Component | Provides |
|---|---|
| `cpp` | `openocean_messages::openocean_messages` |
| `nanopb` | `openocean_messages::nanopb` |
| `lcm` | `openocean_messages::lcm`, and with `cpp`, `openocean_messages::lcm_convert` |
| `python` | `openocean_messages_PYTHON_DIR`, for `PYTHONPATH` |

The package also sets `openocean_messages_PROTO_DIR`, and `CMAKE_MODULE_PATH` gets the generators, so `include(ProtobufGenerateLcm)` or `include(ProtobufGenerateRos)` can generate the project's own protos with `DEPS` naming openocean's (see `src/test/downstream`). Components are found when their files are installed, so separate (e.g. Debian) packages can provide them.

To use a build directory without installing it, point CMake at it: `-Dopenocean_messages_DIR=/path/to/openocean-messages/build`.

### Compatibility checks

*This section was written by Claude.*

CI checks each pull request against its base branch, and the scripts run locally too (`.github/ci/check-abi.sh origin/main`):

| Check | Fails when | Unless |
|---|---|---|
| ABI (`check-abi.sh`, `abidiff`) | a shared library changes other than by additions (adding a field changes a generated class's size, so it counts) | `OPENOCEAN_SOVERSION` is bumped |
| Protobuf (`check-buf.sh`, `buf breaking` with the `FILE` rules in `buf.yaml`) | a proto changes incompatibly, including renames | the version's compatibility component is bumped: the major version, or in `0.y.z` the minor |

### nanopb

*This section was written by Claude.*

`src/openocean/messages/nanopb.options` limits each repeated and string field (e.g. at most 2 `Navigation.speed` and 8 `custom` entries, 32-character strings), so every field is a fixed-size struct member rather than a callback. Messages that exceed a limit fail to encode or decode with nanopb.

### Rust

*This section was written by Claude.*

`rust/` is a Cargo crate whose `build.rs` generates the types with [prost](https://github.com/tokio-rs/prost) from `src/openocean/messages`. It can also be built with cargo directly (`cargo build` in `rust/`, with `protoc` on the `PATH`), or used from another crate as a path dependency. `rust-version` is 1.75 (Ubuntu 24.04's cargo), and `Cargo.lock` pins dependencies that build with it.

### Protobuf to LCM

*This section was written by Claude.*

`protoc-gen-lcm` writes one `.lcm` type per message and enum (package `openocean`, e.g. `navigation_t`, `navigation_geodetic_t`), and `lcm-gen` their C++ types. With `OPENOCEAN_CPP=ON`, it also writes `openocean/lcm_convert.h`, with `to_lcm()` and `from_lcm()` overloads for each message. Types from another package's protos are named by package (`openocean.navigation_t`), and `dep=<proto path prefix>=<converter header>` (`DEPS` in `protobuf_generate_lcm()`) gives the header with their conversions.

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

*This section was written by Claude.*

`protoc-gen-ros` writes two packages: `openocean_msgs`, with the messages, and `openocean_msgs_convert`, which builds the Protobuf C++ library and provides `to_ros()` and `from_ros()` overloads for each message (`#include <openocean_msgs_convert/convert.hpp>`, target `openocean_msgs_convert::openocean_msgs_convert`).

Protos that use another package's protos (e.g. a vendor message with an `openocean.Navigation` field) name that package with `dep=<proto path prefix>=<ROS package>` (`DEPS` in `protobuf_generate_ros()`), e.g. `dep=openocean/messages/=openocean_msgs`. Their fields become `openocean_msgs/Navigation`, and their converter package links `openocean_msgs_convert` (which installs its protos for this) rather than compiling openocean's protos again, which Protobuf would reject in one process.

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

*This section was written by Claude.*

Apache-2.0; see [LICENSE](LICENSE).
