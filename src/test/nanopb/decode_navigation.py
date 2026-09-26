"""Decodes the Navigation that check_messages.c encoded with nanopb, using the
Python Protobuf modules, to check the two are wire compatible."""

import sys

from openocean.messages import common_pb2, navigation_pb2

with open(sys.argv[1], "rb") as f:
    nav = navigation_pb2.Navigation.FromString(f.read())

assert nav.time == 1000000
assert nav.geodetic.latitude == 41.5 and nav.geodetic.depth == 10.0
assert not nav.geodetic.HasField("longitude") and not nav.HasField("enu")
assert len(nav.speed) == 1 and nav.speed[0].value == 1.5
assert nav.speed[0].mode == common_pb2.SPEED_MODE_OVER_GROUND
assert nav.vehicle.name == "auv1"
print("nanopb output decoded by Protobuf Python OK")
