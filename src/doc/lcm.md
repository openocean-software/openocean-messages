# Protobuf to LCM

*This page was written by Claude.*

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
