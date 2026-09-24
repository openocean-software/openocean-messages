cmake_minimum_required(VERSION 3.13...4.2.3 FATAL_ERROR)
project(openocean_messages CXX)

if(((NOT DEFINED CMAKE_CXX_STANDARD) OR ("${CMAKE_CXX_STANDARD}" STREQUAL "03") OR ("${CMAKE_CXX_STANDARD}" STREQUAL "11") OR ("${CMAKE_CXX_STANDARD}" STREQUAL "14")))
  set(CMAKE_CXX_STANDARD 17)
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
endif()

find_package(Protobuf REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(UDUNITS REQUIRED IMPORTED_TARGET udunits)

include(CTest)

add_subdirectory(src)
