"""Round-trips a Navigation through the generated Python Protobuf modules."""

from openocean.messages import common_pb2, navigation_pb2

nav = navigation_pb2.Navigation(time=1_000_000)
nav.geodetic.latitude = 41.5
nav.geodetic.depth = 10.0
nav.speed.add(value=1.5, mode=common_pb2.SPEED_MODE_OVER_GROUND)

parsed = navigation_pb2.Navigation.FromString(nav.SerializeToString())
assert parsed == nav
assert parsed.HasField("geodetic") and not parsed.HasField("enu")
assert parsed.geodetic.HasField("depth") and not parsed.geodetic.HasField("longitude")
print("Python Protobuf messages OK")
