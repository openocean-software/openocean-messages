# Using from another project

*This page was written by Claude.*

## Installing

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

## Using from another project

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

The package also sets `openocean_messages_PROTO_DIR`, and `CMAKE_MODULE_PATH` gets the generators, so `include(ProtobufGenerateLcm)` or `include(ProtobufGenerateRos)` can generate the project's own protos with `DEPS` naming openocean's (see `src/test/downstream`, and [openocean-messages-examples](https://github.com/openocean-software/openocean-messages-examples) for an example of each output). Components are found when their files are installed, so separate (e.g. Debian) packages can provide them.

To use a build directory without installing it, point CMake at it: `-Dopenocean_messages_DIR=/path/to/openocean-messages/build`.
