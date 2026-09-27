cmake_minimum_required(VERSION 3.13...4.2.3 FATAL_ERROR)
project(openocean_messages VERSION 0.1.0 LANGUAGES NONE)

# The shared libraries' ABI version, independent of PROJECT_VERSION. Bump it for any ABI change,
# which for Protobuf and nanopb generated code includes adding a field.
set(OPENOCEAN_SOVERSION 1)

set(OPENOCEAN_CPP_DEFAULT ON)
set(OPENOCEAN_PYTHON_DEFAULT OFF)
set(OPENOCEAN_ROS_DEFAULT OFF)
set(OPENOCEAN_NANOPB_DEFAULT OFF)
set(OPENOCEAN_RUST_DEFAULT OFF)
set(OPENOCEAN_LCM_DEFAULT OFF)
include(${CMAKE_CURRENT_SOURCE_DIR}/init.cmake OPTIONAL)
option(OPENOCEAN_CPP "Build the C++ Protobuf library" ${OPENOCEAN_CPP_DEFAULT})
option(OPENOCEAN_PYTHON "Generate the Python Protobuf modules" ${OPENOCEAN_PYTHON_DEFAULT})
option(OPENOCEAN_ROS "Generate the ROS 2 message package" ${OPENOCEAN_ROS_DEFAULT})
option(OPENOCEAN_NANOPB "Build the nanopb C library" ${OPENOCEAN_NANOPB_DEFAULT})
option(OPENOCEAN_RUST "Build the Rust crate with cargo" ${OPENOCEAN_RUST_DEFAULT})
option(OPENOCEAN_LCM "Generate LCM types (and with OPENOCEAN_CPP, converters to and from Protobuf)" ${OPENOCEAN_LCM_DEFAULT})
option(BUILD_SHARED_LIBS "Build shared libraries" ON)

if(OPENOCEAN_CPP OR OPENOCEAN_LCM)
  enable_language(CXX)
  if(((NOT DEFINED CMAKE_CXX_STANDARD) OR ("${CMAKE_CXX_STANDARD}" STREQUAL "03") OR ("${CMAKE_CXX_STANDARD}" STREQUAL "11") OR ("${CMAKE_CXX_STANDARD}" STREQUAL "14")))
    set(CMAKE_CXX_STANDARD 17)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)
  endif()
endif()

if(OPENOCEAN_CPP)
  find_package(Protobuf REQUIRED)
endif()
include(${PROJECT_SOURCE_DIR}/src/generators/ProtocTarget.cmake)
if(OPENOCEAN_NANOPB)
  enable_language(C)
  find_package(nanopb CONFIG REQUIRED)
  find_program(NANOPB_PROTOC_PLUGIN protoc-gen-nanopb)
  if(NOT NANOPB_PROTOC_PLUGIN)
    message(FATAL_ERROR "protoc-gen-nanopb not found")
  endif()
endif()
if(OPENOCEAN_RUST)
  find_program(CARGO cargo)
  if(NOT CARGO)
    message(FATAL_ERROR "cargo not found")
  endif()
  set(OPENOCEAN_CARGO ${CMAKE_COMMAND} -E env PROTOC=${Protobuf_PROTOC_EXECUTABLE}
    CARGO_TARGET_DIR=${PROJECT_BINARY_DIR}/rust
    ${CARGO} --locked)
  set(OPENOCEAN_CARGO_MANIFEST ${PROJECT_SOURCE_DIR}/rust/Cargo.toml)
endif()
if(OPENOCEAN_PYTHON OR OPENOCEAN_ROS)
  find_package(Python3 REQUIRED COMPONENTS Interpreter)
endif()

if(NOT OPENOCEAN_CPP AND NOT OPENOCEAN_NANOPB AND NOT DEFINED CMAKE_INSTALL_LIBDIR)
  # Without a compiler, GNUInstallDirs can't pick the multiarch directory, and nothing needs it
  set(CMAKE_INSTALL_LIBDIR lib)
endif()
include(GNUInstallDirs)
set(OPENOCEAN_INSTALL_GENERATORS_DIR ${CMAKE_INSTALL_DATADIR}/openocean_messages/generators)
# Debian's directory for Python 3 modules, which works for every Python 3 version
set(OPENOCEAN_INSTALL_PYTHON_DIR lib/python3/dist-packages CACHE PATH
  "Python module installation directory, relative to CMAKE_INSTALL_PREFIX")
if(OPENOCEAN_CPP OR OPENOCEAN_NANOPB)
  set(OPENOCEAN_INSTALL_CMAKE_DIR ${CMAKE_INSTALL_LIBDIR}/cmake/openocean_messages)
else()
  set(OPENOCEAN_INSTALL_CMAKE_DIR ${CMAKE_INSTALL_DATADIR}/cmake/openocean_messages)
endif()

include(CTest)

add_subdirectory(src)

include(CMakePackageConfigHelpers)
# As Cargo does, treat 0.y as the compatibility component before 1.0
if(PROJECT_VERSION_MAJOR EQUAL 0)
  set(compatibility SameMinorVersion)
else()
  set(compatibility SameMajorVersion)
endif()
write_basic_package_version_file(${PROJECT_BINARY_DIR}/openocean_messages-config-version.cmake
  COMPATIBILITY ${compatibility})

set(export_sets)
if(OPENOCEAN_CPP)
  list(APPEND export_sets cpp)
endif()
if(OPENOCEAN_NANOPB)
  list(APPEND export_sets nanopb)
endif()
if(OPENOCEAN_LCM)
  list(APPEND export_sets lcm)
endif()
foreach(set IN LISTS export_sets)
  install(EXPORT openocean_messages-${set}-targets NAMESPACE openocean_messages::
    DESTINATION ${OPENOCEAN_INSTALL_CMAKE_DIR})
  export(EXPORT openocean_messages-${set}-targets NAMESPACE openocean_messages::
    FILE ${PROJECT_BINARY_DIR}/openocean_messages-${set}-targets.cmake)
endforeach()

set(config_template ${PROJECT_SOURCE_DIR}/cmake/openocean_messages-config.cmake.in)
set(OPENOCEAN_CONFIG_PROTO_DIR ${CMAKE_INSTALL_INCLUDEDIR})
set(OPENOCEAN_CONFIG_GENERATORS_DIR ${OPENOCEAN_INSTALL_GENERATORS_DIR})
set(OPENOCEAN_CONFIG_PYTHON_DIR ${OPENOCEAN_INSTALL_PYTHON_DIR})
configure_package_config_file(${config_template}
  ${PROJECT_BINARY_DIR}/CMakeFiles/install/openocean_messages-config.cmake
  INSTALL_DESTINATION ${OPENOCEAN_INSTALL_CMAKE_DIR}
  PATH_VARS OPENOCEAN_CONFIG_PROTO_DIR OPENOCEAN_CONFIG_GENERATORS_DIR OPENOCEAN_CONFIG_PYTHON_DIR)
install(FILES
  ${PROJECT_BINARY_DIR}/CMakeFiles/install/openocean_messages-config.cmake
  ${PROJECT_BINARY_DIR}/openocean_messages-config-version.cmake
  DESTINATION ${OPENOCEAN_INSTALL_CMAKE_DIR})

# So that downstream projects can use this build directory without installing it
set(OPENOCEAN_CONFIG_PROTO_DIR ${PROJECT_SOURCE_DIR}/src)
set(OPENOCEAN_CONFIG_GENERATORS_DIR ${PROJECT_SOURCE_DIR}/src/generators)
set(OPENOCEAN_CONFIG_PYTHON_DIR ${PROJECT_BINARY_DIR}/python)
configure_package_config_file(${config_template}
  ${PROJECT_BINARY_DIR}/openocean_messages-config.cmake
  INSTALL_DESTINATION ${PROJECT_BINARY_DIR}
  INSTALL_PREFIX ${PROJECT_BINARY_DIR}
  PATH_VARS OPENOCEAN_CONFIG_PROTO_DIR OPENOCEAN_CONFIG_GENERATORS_DIR OPENOCEAN_CONFIG_PYTHON_DIR)
