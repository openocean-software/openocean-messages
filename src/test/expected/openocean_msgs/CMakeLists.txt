cmake_minimum_required(VERSION 3.8)
project(openocean_msgs)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/ControlSetpoint.msg"
  "msg/ControlSetpointCustomSetpoint.msg"
  "msg/Euler.msg"
  "msg/Navigation.msg"
  "msg/NavigationAcceleration.msg"
  "msg/NavigationAngularAcceleration.msg"
  "msg/NavigationAngularVelocity.msg"
  "msg/NavigationENU.msg"
  "msg/NavigationGeodetic.msg"
  "msg/NavigationVehicleMetadata.msg"
  "msg/NavigationVelocity.msg"
  "msg/Speed.msg"
  "msg/SpeedMode.msg"
  DEPENDENCIES builtin_interfaces
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
