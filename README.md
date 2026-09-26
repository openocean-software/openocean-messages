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
  - test: Checks that all units parse with UDUNITS-2 and that fields ControlSetpoint shares with Navigation have the same type and units, and tests for each output

## Conventions

- Geodetic position is latitude, longitude, and depth (positive down)
- Local position is ENU e, n, u about a datum (u = -depth)
- Body-frame velocities are forward, starboard, down (Fossen / SNAME)
- Heading and course are clockwise from true north
- Unset optional fields are unknown (Navigation) or not controlled (ControlSetpoint)

## Building

Install the dependencies (Ubuntu) for the outputs you want, then build with CMake and Ninja:

```
./init.sh --cxx --python --ros --nanopb
./build.sh
ctest --test-dir build
```

`build.sh` passes any arguments on to CMake, and `BUILD_DIR` overrides the build directory (default `build`).

### Outputs

| `init.sh` | CMake option | Default | Output |
|---|---|---|---|
| `--cxx` | `OPENOCEAN_CPP` | ON | `openocean_messages` library (`#include "openocean/messages/navigation.pb.h"`) |
| `--python` | `OPENOCEAN_PYTHON` | OFF | `build/python` (`from openocean.messages import navigation_pb2`) |
| `--ros` | `OPENOCEAN_ROS` | OFF | `build/ros/openocean_msgs` ROS 2 package source, to build with colcon |
| `--nanopb` | `OPENOCEAN_NANOPB` | OFF | `openocean_messages_nanopb` C library (`#include "openocean/messages/navigation.pb.h"`, from `build/nanopb`) |

`init.sh` with no options is `--cxx`. It writes `init.cmake`, which sets the option defaults for new build directories to the outputs it installed; `-D` still overrides them.

For example, with ROS 2 sourced:

```
./init.sh --ros
./build.sh
colcon build --base-paths build/ros
```

### nanopb

`src/openocean/messages/nanopb.options` limits each repeated and string field (e.g. at most 2 `Navigation.speed` entries, 32-character strings), so every field is a fixed-size struct member rather than a callback. Messages that exceed a limit fail to encode or decode with nanopb.

### Protobuf to ROS 2

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

Field names that are Python or C++ keywords are rejected. `src/test/expected` holds the package the generator should produce from `src/test/ros/mapping.proto`; after an intended change to the generator, run `ninja -C build update_expected` and review the diff.

## License

Apache-2.0; see [LICENSE](LICENSE).
