# Protobuf to ROS 2

*This page was written by Claude.*

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
