cmake_minimum_required(VERSION 3.10)
project(openocean_msgs_check CXX)

find_package(ament_cmake REQUIRED)
find_package(openocean_msgs REQUIRED)
find_package(openocean_test_msgs REQUIRED)
find_package(openocean_msgs_convert REQUIRED)
find_package(openocean_test_msgs_convert REQUIRED)

add_executable(check_messages check_messages.cpp)
target_link_libraries(check_messages
  ${openocean_msgs_TARGETS}
  ${openocean_test_msgs_TARGETS})
# Separate executables, since both converter packages build options.proto into their Protobuf
# library, and Protobuf refuses to register the same file twice in one process
add_executable(check_convert check_convert.cpp)
target_link_libraries(check_convert openocean_msgs_convert::openocean_msgs_convert)
add_executable(check_convert_mapping check_convert_mapping.cpp)
target_link_libraries(check_convert_mapping openocean_test_msgs_convert::openocean_test_msgs_convert)

install(TARGETS check_messages check_convert check_convert_mapping DESTINATION lib/${PROJECT_NAME})

ament_package()
