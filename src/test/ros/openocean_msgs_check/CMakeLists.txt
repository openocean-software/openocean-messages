cmake_minimum_required(VERSION 3.10)
project(openocean_msgs_check CXX)

find_package(ament_cmake REQUIRED)
find_package(openocean_msgs REQUIRED)
find_package(openocean_test_msgs REQUIRED)

add_executable(check_messages check_messages.cpp)
target_link_libraries(check_messages
  ${openocean_msgs_TARGETS}
  ${openocean_test_msgs_TARGETS})
install(TARGETS check_messages DESTINATION lib/${PROJECT_NAME})

ament_package()
