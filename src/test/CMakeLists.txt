add_test(NAME version_consistent
  COMMAND ${CMAKE_COMMAND} -DPROJECT_VERSION=${PROJECT_VERSION}
          -DCARGO_TOML=${PROJECT_SOURCE_DIR}/rust/Cargo.toml -P ${CMAKE_CURRENT_SOURCE_DIR}/check_version.cmake)

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
    OPTIONS ${OPENOCEAN_ROS_OPTIONS}
    DEPS openocean/messages/=${OPENOCEAN_ROS_PACKAGE}
    CONVERT_PACKAGE openocean_test_msgs_convert)

  set(expected ${CMAKE_CURRENT_SOURCE_DIR}/expected/openocean_test_msgs)
  set(expected_convert ${CMAKE_CURRENT_SOURCE_DIR}/expected/openocean_test_msgs_convert)
  set(convert ${ros_test_dir}/openocean_test_msgs_convert)
  # Only what protoc-gen-ros writes: the converter package's protos are copies of the sources
  add_test(NAME ros_expected COMMAND sh -c
    "diff -r ${expected} ${ros_test_dir}/openocean_test_msgs && \
     diff -r ${expected_convert}/include ${convert}/include && \
     diff -r ${expected_convert}/cmake ${convert}/cmake && \
     diff ${expected_convert}/package.xml ${convert}/package.xml && \
     diff ${expected_convert}/CMakeLists.txt ${convert}/CMakeLists.txt")
  list(APPEND update_expected
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${expected}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${ros_test_dir}/openocean_test_msgs ${expected}
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${expected_convert}
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${convert}/include ${expected_convert}/include
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${convert}/cmake ${expected_convert}/cmake
    COMMAND ${CMAKE_COMMAND} -E copy ${convert}/package.xml ${convert}/CMakeLists.txt ${expected_convert})
  list(APPEND update_expected_depends openocean_test_msgs_ros)

  find_program(COLCON colcon)
  if(COLCON AND DEFINED ENV{AMENT_PREFIX_PATH})
    add_test(NAME ros_build
      COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/ros/build_and_check.sh
              ${CMAKE_CURRENT_BINARY_DIR}/ros_ws ${Python3_EXECUTABLE}
              ${OPENOCEAN_ROS_DIR} ${ros_test_dir})
  else()
    message(STATUS "colcon or a sourced ROS 2 environment not found: skipping the ros_build test")
  endif()
endif()

if(OPENOCEAN_LCM)
  set(lcm_test_dir ${CMAKE_CURRENT_BINARY_DIR}/lcm)
  set(converter)
  if(OPENOCEAN_CPP)
    add_library(openocean_test_messages)
    protobuf_generate(
      TARGET openocean_test_messages
      LANGUAGE cpp
      PROTOS mapping.proto
      IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/src
      PROTOC_OUT_DIR ${CMAKE_CURRENT_BINARY_DIR})
    target_include_directories(openocean_test_messages PUBLIC ${CMAKE_CURRENT_BINARY_DIR})
    target_link_libraries(openocean_test_messages PUBLIC openocean_messages)
    set(converter
      CONVERTER_TARGET openocean_test_messages_lcm_convert
      HEADER openocean/test/lcm_convert.h
      LINK_LIBRARIES openocean_test_messages openocean_messages_lcm_convert)
  endif()
  protobuf_generate_lcm(
    TARGET openocean_test_messages_lcm
    OUTPUT_DIR ${lcm_test_dir}
    PROTOS mapping.proto
    IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/src
    DEPS openocean/messages/=openocean/lcm_convert.h
    LINK_TYPES openocean_messages_lcm
    ${converter})

  add_executable(check_lcm_types lcm/check_types.cpp)
  target_link_libraries(check_lcm_types PRIVATE openocean_messages_lcm openocean_test_messages_lcm)
  add_test(NAME lcm_types COMMAND check_lcm_types)

  set(expected ${CMAKE_CURRENT_SOURCE_DIR}/expected/lcm)
  if(OPENOCEAN_CPP)
    add_executable(check_lcm_convert lcm/check_convert.cpp)
    target_link_libraries(check_lcm_convert PRIVATE
      openocean_messages_lcm_convert openocean_test_messages_lcm_convert)
    add_test(NAME lcm_convert COMMAND check_lcm_convert)

    add_test(NAME lcm_expected COMMAND diff -r ${expected} ${lcm_test_dir}/protoc-gen-lcm)
    list(APPEND update_expected
      COMMAND ${CMAKE_COMMAND} -E remove_directory ${expected}
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${lcm_test_dir}/protoc-gen-lcm ${expected})
    list(APPEND update_expected_depends openocean_test_messages_lcm_generate)
  else()
    # Without the converter header (in expected/lcm/openocean), only the .lcm types to compare
    add_test(NAME lcm_expected
      COMMAND diff -r -x openocean ${expected} ${lcm_test_dir}/protoc-gen-lcm)
  endif()
endif()

# A downstream project, against this build directory and against an installation of it
set(downstream_options -DOPENOCEAN_VERSION=${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR})
foreach(output CPP NANOPB LCM PYTHON ROS)
  list(APPEND downstream_options -DWITH_${output}=${OPENOCEAN_${output}})
endforeach()
set(install_dir ${CMAKE_CURRENT_BINARY_DIR}/install)
add_test(NAME install
  COMMAND ${CMAKE_COMMAND} -E env DESTDIR=
          ${CMAKE_COMMAND} --install ${PROJECT_BINARY_DIR} --prefix ${install_dir})
set_tests_properties(install PROPERTIES FIXTURES_SETUP install)
foreach(tree build install)
  if(tree STREQUAL build)
    set(find_option -Dopenocean_messages_DIR=${PROJECT_BINARY_DIR})
  else()
    set(find_option -DCMAKE_PREFIX_PATH=${install_dir})
  endif()
  add_test(NAME downstream_${tree}_tree
    COMMAND ${CMAKE_CTEST_COMMAND}
            --build-and-test ${CMAKE_CURRENT_SOURCE_DIR}/downstream
                             ${CMAKE_CURRENT_BINARY_DIR}/downstream_${tree}
            --build-generator ${CMAKE_GENERATOR}
            --build-options ${find_option} ${downstream_options}
            --test-command ${CMAKE_CTEST_COMMAND} --output-on-failure --no-tests=ignore)
endforeach()
set_tests_properties(downstream_install_tree PROPERTIES FIXTURES_REQUIRED install)

# Asking only for python must not need a compiler, which the other components' dependencies do
if(OPENOCEAN_PYTHON)
  add_test(NAME downstream_python_only
    COMMAND ${CMAKE_CTEST_COMMAND}
            --build-and-test ${CMAKE_CURRENT_SOURCE_DIR}/downstream
                             ${CMAKE_CURRENT_BINARY_DIR}/downstream_python_only
            --build-generator ${CMAKE_GENERATOR}
            --build-options -Dopenocean_messages_DIR=${PROJECT_BINARY_DIR} -DWITH_PYTHON=ON
            --test-command ${CMAKE_CTEST_COMMAND} --output-on-failure)
endif()

if(update_expected)
  add_custom_target(update_expected ${update_expected}
    COMMENT "Updating ${CMAKE_CURRENT_SOURCE_DIR}/expected"
    VERBATIM)
  add_dependencies(update_expected ${update_expected_depends})
endif()
