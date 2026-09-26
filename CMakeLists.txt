cmake_minimum_required(VERSION 3.13...4.2.3 FATAL_ERROR)
project(openocean_messages CXX)

if(((NOT DEFINED CMAKE_CXX_STANDARD) OR ("${CMAKE_CXX_STANDARD}" STREQUAL "03") OR ("${CMAKE_CXX_STANDARD}" STREQUAL "11") OR ("${CMAKE_CXX_STANDARD}" STREQUAL "14")))
  set(CMAKE_CXX_STANDARD 17)
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
endif()

option(OPENOCEAN_CPP "Build the C++ Protobuf library" ON)
option(OPENOCEAN_PYTHON "Generate the Python Protobuf modules" OFF)
option(OPENOCEAN_ROS "Generate the ROS 2 message package" OFF)

find_package(Protobuf REQUIRED)
if(OPENOCEAN_PYTHON OR OPENOCEAN_ROS)
  find_package(Python3 REQUIRED COMPONENTS Interpreter)
endif()

include(CTest)

add_subdirectory(src)
