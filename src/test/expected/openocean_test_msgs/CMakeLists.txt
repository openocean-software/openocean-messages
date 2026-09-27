cmake_minimum_required(VERSION 3.10)
project(openocean_test_msgs VERSION 0.1.0)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(openocean_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Mapping.msg"
  "msg/MappingByIdEntry.msg"
  "msg/MappingColor.msg"
  "msg/MappingInner.msg"
  "msg/MappingSigned.msg"
  "msg/MappingTableEntry.msg"
  DEPENDENCIES builtin_interfaces openocean_msgs
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
