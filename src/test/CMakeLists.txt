if(OPENOCEAN_CPP)
  find_package(PkgConfig REQUIRED)
  pkg_check_modules(UDUNITS REQUIRED IMPORTED_TARGET udunits)
  add_executable(check_units check_units.cpp)
  target_link_libraries(check_units PRIVATE openocean_messages PkgConfig::UDUNITS)
  add_test(NAME check_units COMMAND check_units)
endif()

if(OPENOCEAN_PYTHON)
  add_test(NAME python_messages
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/python/check_messages.py)
  set_tests_properties(python_messages PROPERTIES ENVIRONMENT PYTHONPATH=${OPENOCEAN_PYTHON_DIR})
endif()

if(OPENOCEAN_NANOPB)
  add_executable(check_nanopb nanopb/check_messages.c)
  target_link_libraries(check_nanopb PRIVATE openocean_messages_nanopb)
  set(nanopb_navigation ${CMAKE_CURRENT_BINARY_DIR}/nanopb_navigation.bin)
  add_test(NAME nanopb_messages COMMAND check_nanopb ${nanopb_navigation})
  if(OPENOCEAN_PYTHON)
    set_tests_properties(nanopb_messages PROPERTIES FIXTURES_SETUP nanopb_navigation)
    add_test(NAME nanopb_python_decode
      COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/nanopb/decode_navigation.py
              ${nanopb_navigation})
    set_tests_properties(nanopb_python_decode PROPERTIES
      ENVIRONMENT PYTHONPATH=${OPENOCEAN_PYTHON_DIR}
      FIXTURES_REQUIRED nanopb_navigation)
  endif()
endif()

if(OPENOCEAN_RUST)
  add_test(NAME rust_messages
    COMMAND ${OPENOCEAN_CARGO} test --manifest-path ${OPENOCEAN_CARGO_MANIFEST})
endif()

if(OPENOCEAN_ROS)
  set(ros_test_dir ${CMAKE_CURRENT_BINARY_DIR}/ros)
  protobuf_generate_ros(
    TARGET openocean_test_msgs_ros
    PACKAGE openocean_test_msgs
    OUTPUT_DIR ${ros_test_dir}
    PROTOS mapping.proto
    IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/src
    OPTIONS ${OPENOCEAN_ROS_OPTIONS})

  set(expected ${CMAKE_CURRENT_SOURCE_DIR}/expected/openocean_test_msgs)
  add_test(NAME ros_expected COMMAND diff -r ${expected} ${ros_test_dir}/openocean_test_msgs)
  list(APPEND update_expected
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${expected}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${ros_test_dir}/openocean_test_msgs ${expected})
  list(APPEND update_expected_depends openocean_test_msgs_ros)

  find_program(COLCON colcon)
  if(COLCON AND DEFINED ENV{AMENT_PREFIX_PATH})
    add_test(NAME ros_build
      COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/ros/build_and_check.sh
              ${CMAKE_CURRENT_BINARY_DIR}/ros_ws ${Python3_EXECUTABLE}
              ${OPENOCEAN_ROS_DIR}/${OPENOCEAN_ROS_PACKAGE} ${ros_test_dir}/openocean_test_msgs)
  else()
    message(STATUS "colcon or a sourced ROS 2 environment not found: skipping the ros_build test")
  endif()
endif()

if(OPENOCEAN_LCM)
  add_library(openocean_test_messages)
  protobuf_generate(
    TARGET openocean_test_messages
    LANGUAGE cpp
    PROTOS mapping.proto
    IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/src
    PROTOC_OUT_DIR ${CMAKE_CURRENT_BINARY_DIR})
  target_include_directories(openocean_test_messages PUBLIC ${CMAKE_CURRENT_BINARY_DIR})
  target_link_libraries(openocean_test_messages PUBLIC openocean_messages)

  set(lcm_test_dir ${CMAKE_CURRENT_BINARY_DIR}/lcm)
  protobuf_generate_lcm(
    TARGET openocean_test_messages_lcm
    OUTPUT_DIR ${lcm_test_dir}
    HEADER openocean/test/lcm_convert.h
    PROTOS mapping.proto
    IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/src
    LINK_LIBRARIES openocean_test_messages)

  add_executable(check_lcm lcm/check_messages.cpp)
  target_link_libraries(check_lcm PRIVATE openocean_messages_lcm openocean_test_messages_lcm)
  add_test(NAME lcm_messages COMMAND check_lcm)

  set(expected ${CMAKE_CURRENT_SOURCE_DIR}/expected/lcm)
  add_test(NAME lcm_expected COMMAND diff -r ${expected} ${lcm_test_dir}/protoc-gen-lcm)
  list(APPEND update_expected
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${expected}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${lcm_test_dir}/protoc-gen-lcm ${expected})
  list(APPEND update_expected_depends openocean_test_messages_lcm_generate)
endif()

if(update_expected)
  add_custom_target(update_expected ${update_expected}
    COMMENT "Updating ${CMAKE_CURRENT_SOURCE_DIR}/expected"
    VERBATIM)
  add_dependencies(update_expected ${update_expected_depends})
endif()
