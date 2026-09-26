# Generated from openocean.Navigation (openocean/messages/navigation.proto)
#
# Frames:
#  - geodetic: WGS-84 latitude, longitude, and depth (positive down)
#  - enu: ENU e (east), n (north), u (up) relative to the datum,
#    so u = -depth
#  - body: x forward, y starboard, z down (Fossen / SNAME)

builtin_interfaces/Time time
bool has_vehicle
NavigationVehicleMetadata vehicle
bool has_geodetic
NavigationGeodetic geodetic
bool has_enu
NavigationENU enu

# defined in common.proto
bool has_attitude
Euler attitude

# repeated so that speed over water and/or speed over ground can be reported
Speed[] speed

# ditto for dx/dt, etc. velocities
NavigationVelocity[] velocity
bool has_altitude
float64 altitude  # [m]
bool has_course_over_ground
float64 course_over_ground  # [rad]
bool has_angular_velocity
NavigationAngularVelocity angular_velocity
bool has_acceleration
NavigationAcceleration acceleration
bool has_angular_acceleration
NavigationAngularAcceleration angular_acceleration
