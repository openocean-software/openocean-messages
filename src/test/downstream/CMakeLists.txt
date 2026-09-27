# A project that uses openocean_messages as a downstream project would: with find_package(), from
# this build directory (openocean_messages_DIR) or an installation (CMAKE_PREFIX_PATH). WITH_CPP,
# WITH_NANOPB, WITH_LCM, WITH_PYTHON, and WITH_ROS select the outputs to check.
cmake_minimum_required(VERSION 3.13...4.2.3 FATAL_ERROR)
project(openocean_downstream LANGUAGES NONE)

if(WITH_CPP OR WITH_LCM)
  enable_language(CXX)
  set(CMAKE_CXX_STANDARD 17)
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
endif()
if(WITH_NANOPB)
  enable_language(C)
endif()

set(components)
foreach(component cpp nanopb lcm python)
  string(TOUPPER ${component} option)
  if(WITH_${option})
    list(APPEND components ${component})
  endif()
endforeach()
find_package(openocean_messages ${OPENOCEAN_VERSION} REQUIRED COMPONENTS ${components})

enable_testing()

set(import_dirs ${CMAKE_CURRENT_SOURCE_DIR} ${openocean_messages_PROTO_DIR})

# Generates only report.proto, and links openocean's library for the protos it imports
if(WITH_CPP)
  add_library(downstream_messages)
  protobuf_generate(
    TARGET downstream_messages
    LANGUAGE cpp
    PROTOS downstream/report.proto
    IMPORT_DIRS ${import_dirs}
    PROTOC_OUT_DIR ${CMAKE_CURRENT_BINARY_DIR})
  target_include_directories(downstream_messages PUBLIC ${CMAKE_CURRENT_BINARY_DIR})
  target_link_libraries(downstream_messages PUBLIC openocean_messages::openocean_messages)
  add_executable(check_cpp check_cpp.cpp)
  target_link_libraries(check_cpp PRIVATE downstream_messages)
  add_test(NAME cpp COMMAND check_cpp)
endif()

if(WITH_NANOPB)
  add_executable(check_nanopb check_nanopb.c)
  target_link_libraries(check_nanopb PRIVATE openocean_messages::nanopb)
  add_test(NAME nanopb COMMAND check_nanopb)
endif()

if(WITH_LCM)
  include(ProtobufGenerateLcm)
  set(converter)
  if(WITH_CPP)
    set(converter
      CONVERTER_TARGET downstream_lcm_convert
      HEADER downstream/lcm_convert.h
      LINK_LIBRARIES downstream_messages openocean_messages::lcm_convert)
  endif()
  protobuf_generate_lcm(
    TARGET downstream_lcm
    OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR}/lcm
    PROTOS downstream/report.proto
    IMPORT_DIRS ${import_dirs}
    DEPS openocean/messages/=openocean/lcm_convert.h
    LINK_TYPES openocean_messages::lcm
    ${converter})
  add_executable(check_lcm check_lcm.cpp)
  target_link_libraries(check_lcm PRIVATE downstream_lcm)
  if(WITH_CPP)
    target_link_libraries(check_lcm PRIVATE downstream_lcm_convert)
    target_compile_definitions(check_lcm PRIVATE WITH_CPP)
  endif()
  add_test(NAME lcm COMMAND check_lcm)
endif()

if(WITH_PYTHON)
  find_package(Python3 REQUIRED COMPONENTS Interpreter)
  add_test(NAME python COMMAND ${Python3_EXECUTABLE} -c
    "from openocean.messages import navigation_pb2; navigation_pb2.Navigation(time=1)")
  set_tests_properties(python PROPERTIES ENVIRONMENT PYTHONPATH=${openocean_messages_PYTHON_DIR})
endif()

# Generation only: building the packages needs colcon, as the ros_build test does
if(WITH_ROS)
  include(ProtobufGenerateRos)
  protobuf_generate_ros(
    TARGET downstream_msgs
    PACKAGE downstream_msgs
    OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR}/ros
    PROTOS downstream/report.proto
    IMPORT_DIRS ${import_dirs}
    OPTIONS maintainer=Nobody maintainer_email=nobody@example.com license=Apache-2.0
    DEPS openocean/messages/=openocean_msgs
    CONVERT_PACKAGE downstream_msgs_convert)
  add_test(NAME ros COMMAND ${CMAKE_COMMAND} -E cat
    ${CMAKE_CURRENT_BINARY_DIR}/ros/downstream_msgs/msg/Report.msg)
  set_tests_properties(ros PROPERTIES PASS_REGULAR_EXPRESSION "openocean_msgs/Navigation navigation")
endif()
