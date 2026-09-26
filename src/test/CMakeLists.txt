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

if(OPENOCEAN_ROS)
  set(ros_test_dir ${CMAKE_CURRENT_BINARY_DIR}/ros)
  protobuf_generate_ros(
    TARGET openocean_test_msgs_ros
    PACKAGE openocean_test_msgs
    OUTPUT_DIR ${ros_test_dir}
    PROTOS ros/mapping.proto
    IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/ros ${PROJECT_SOURCE_DIR}/src
    OPTIONS ${OPENOCEAN_ROS_OPTIONS})

  set(expected ${CMAKE_CURRENT_SOURCE_DIR}/expected/openocean_test_msgs)
  add_test(NAME ros_expected COMMAND diff -r ${expected} ${ros_test_dir}/openocean_test_msgs)
  add_custom_target(update_expected
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${expected}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${ros_test_dir}/openocean_test_msgs ${expected}
    COMMENT "Updating ${expected}"
    VERBATIM)
  add_dependencies(update_expected openocean_test_msgs_ros)

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
