# Generated from openocean.ControlSetpoint (openocean/messages/control.proto)
#
# Quantities and frames match Navigation.

builtin_interfaces/Time time
bool has_attitude
Euler attitude
bool has_speed
Speed speed
bool has_depth
float64 depth  # [m]

# above the seafloor
bool has_altitude
float64 altitude  # [m]
ControlSetpointCustomSetpoint[] custom
