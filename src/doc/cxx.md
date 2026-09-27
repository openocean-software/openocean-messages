# C++

*This page was written by Claude.*

`OPENOCEAN_CPP` (`init.sh --cxx`, on by default) builds the `openocean_messages` library from the protos with Protobuf's C++ generator. Types are in the `openocean` namespace, and headers are `openocean/messages/*.pb.h`:

```cpp
#include "openocean/messages/navigation.pb.h"

openocean::Navigation nav;
nav.mutable_geodetic()->set_latitude(41.52);
nav.mutable_attitude()->set_heading(1.57); // radians
nav.geodetic().has_depth(); // false: optional fields have presence
```

Units are in the descriptors, so code can read them at runtime:

```cpp
#include "openocean/messages/options.pb.h"

const auto* depth = openocean::Navigation::Geodetic::descriptor()->FindFieldByName("depth");
depth->options().GetExtension(openocean::field).units(); // "m"
```

Downstream projects link `openocean_messages::openocean_messages` (`find_package(openocean_messages COMPONENTS cpp)`), including for their own protos that import openocean's; see [Using from another project](using.md). The library is shared by default (`-DBUILD_SHARED_LIBS=OFF` for static), with `OPENOCEAN_SOVERSION` as its ABI version.

The [ROS 2](ros.md) and [LCM](lcm.md) converters convert to and from these types.

Examples: [protobuf/cxx](https://github.com/openocean-software/openocean-messages-examples/tree/main/protobuf/cxx) and [protobuf/composition](https://github.com/openocean-software/openocean-messages-examples/tree/main/protobuf/composition).
