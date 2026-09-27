"""Checks the generated ROS 2 Python types, which is where Python keywords as
field names would fail (at import)."""

from openocean_msgs.msg import ControlSetpoint, Navigation, SpeedMode
from openocean_test_msgs.msg import Mapping, MappingColor

nav = Navigation()
assert nav.has_geodetic is False
nav.has_enu = True
nav.enu.e = 1.0
assert SpeedMode.OVER_GROUND == 1
assert MappingColor.GREEN == 1
assert Mapping.CHOICE_B == 13
ControlSetpoint(has_depth=True, depth=5.0)
print("ROS 2 Python messages OK")
