# Building

*This page was written by Claude.*

Install the dependencies (Ubuntu) for the outputs you want, then build with CMake and Ninja:

```
./init.sh --cxx --python --ros --nanopb --rust --lcm
./build.sh
ctest --test-dir build
```

`build.sh` passes any arguments on to CMake, and `BUILD_DIR` overrides the build directory (default `build`).

## Outputs

| `init.sh` | CMake option (Boolean)  | Output |
|---|---|---|
| `--cxx` | `OPENOCEAN_CPP`  | [C++](cxx.md): `openocean_messages` library (`#include "openocean/messages/navigation.pb.h"`) |
| `--python` | `OPENOCEAN_PYTHON`  | [Python](python.md): `build/python` (`from openocean.messages import navigation_pb2`) |
| `--ros` | `OPENOCEAN_ROS`  | [ROS 2](ros.md): `build/ros/openocean_msgs` and `build/ros/openocean_msgs_convert` ROS 2 package sources, to build with colcon |
| `--nanopb` | `OPENOCEAN_NANOPB`  | [nanopb](nanopb.md): `openocean_messages_nanopb` C library (`#include "openocean/messages/navigation.pb.h"`, from `build/nanopb`) |
| `--rust` | `OPENOCEAN_RUST`  | [Rust](rust.md): `openocean-messages` crate in `rust/` (prost), built into `build/rust` |
| `--lcm` | `OPENOCEAN_LCM`  | [LCM](lcm.md): `openocean_messages_lcm` LCM types (`#include "openocean/navigation_t.hpp"`); *with* `--cxx`, also `openocean_messages_lcm_convert` (`#include "openocean/lcm_convert.h"`) |

Libraries build shared by default (`-DBUILD_SHARED_LIBS=OFF` builds them static), as do the generated ROS 2 converter packages. The version (`project(VERSION)` in `CMakeLists.txt`) carries through to the libraries, the ROS 2 packages, and the Rust crate (checked by the `version_consistent` test). `OPENOCEAN_SOVERSION` is the shared libraries' ABI version.

`init.sh` with no options is `--cxx`. It writes `init.cmake`, which sets the option defaults for new build directories to the outputs it installed; `-D` still overrides them.

For example, with ROS 2 sourced:

```
./init.sh --ros
./build.sh
colcon build --base-paths build/ros
```
