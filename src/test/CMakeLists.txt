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

if(OPENOCEAN_ROS)
  set(ros_test_dir ${CMAKE_CURRENT_BINARY_DIR}/ros)
  protobuf_generate_ros(
    TARGET openocean_test_msgs_ros
    PACKAGE openocean_test_msgs
    OUTPUT_DIR ${ros_test_dir}
    PROTOS ros/mapping.proto
    IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/ros ${PROJECT_SOURCE_DIR}/src
    OPTIONS ${OPENOCEAN_ROS_OPTIONS})

  # To accept intended changes, copy the generated packages over golden/
  foreach(package ${OPENOCEAN_ROS_DIR}/${OPENOCEAN_ROS_PACKAGE} ${ros_test_dir}/openocean_test_msgs)
    get_filename_component(name ${package} NAME)
    add_test(NAME ros_golden_${name}
      COMMAND diff -r ${CMAKE_CURRENT_SOURCE_DIR}/golden/${name} ${package})
  endforeach()

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
