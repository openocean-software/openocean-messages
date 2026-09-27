# Python

*This page was written by Claude.*

`OPENOCEAN_PYTHON` (`init.sh --python`) generates the Python modules with `protoc --python_out` into `build/python`, as the `openocean.messages` package. They need only Protobuf's Python runtime (`python3-protobuf`), not a compiler:

```python
from openocean.messages import navigation_pb2

nav = navigation_pb2.Navigation()
nav.geodetic.latitude = 41.52
nav.attitude.heading = 1.57  # radians
nav.geodetic.HasField("depth")  # False: optional fields have presence
```

Units are in the descriptors, so code can read them at runtime:

```python
from openocean.messages import options_pb2

depth = navigation_pb2.Navigation.Geodetic.DESCRIPTOR.fields_by_name["depth"]
depth.GetOptions().Extensions[options_pb2.field].units  # "m"
```

`cmake --install` puts the modules in `lib/python3/dist-packages` (`OPENOCEAN_INSTALL_PYTHON_DIR`), which is on Debian's Python path when the prefix is `/usr`. Otherwise, add the directory to `PYTHONPATH`: `find_package(openocean_messages COMPONENTS python)` sets `openocean_messages_PYTHON_DIR` to it, for the installation or the build directory.

Example: [protobuf/python](https://github.com/openocean-software/openocean-messages-examples/tree/main/protobuf/python).
