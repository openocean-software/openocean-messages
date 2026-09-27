set(OPENOCEAN_PROTOS
  openocean/messages/options.proto
  openocean/messages/common.proto
  openocean/messages/navigation.proto
  openocean/messages/control.proto)

# In the include directory, so the import paths match the C++ #include paths
install(FILES ${OPENOCEAN_PROTOS} openocean/messages/nanopb.options
  DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/openocean/messages)
install(PROGRAMS generators/protoc-gen-ros generators/protoc-gen-lcm
  DESTINATION ${OPENOCEAN_INSTALL_GENERATORS_DIR})
install(FILES
  generators/ProtocTarget.cmake
  generators/ProtobufGenerateRos.cmake
  generators/ProtobufGenerateLcm.cmake
  generators/GenerateLcm.cmake
  DESTINATION ${OPENOCEAN_INSTALL_GENERATORS_DIR})
install(DIRECTORY generators/openocean_gen DESTINATION ${OPENOCEAN_INSTALL_GENERATORS_DIR}
  PATTERN __pycache__ EXCLUDE)

if(OPENOCEAN_CPP)
  add_library(openocean_messages)
  set_target_properties(openocean_messages PROPERTIES
    VERSION ${PROJECT_VERSION} SOVERSION ${OPENOCEAN_SOVERSION})
  protobuf_generate(
    TARGET openocean_messages
    LANGUAGE cpp
    PROTOS ${OPENOCEAN_PROTOS}
    IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR}
    PROTOC_OUT_DIR ${CMAKE_CURRENT_BINARY_DIR})
  target_include_directories(openocean_messages PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)
  target_link_libraries(openocean_messages PUBLIC protobuf::libprotobuf)

  set(headers)
  foreach(proto IN LISTS OPENOCEAN_PROTOS)
    string(REGEX REPLACE "\\.proto$" ".pb.h" header ${proto})
    list(APPEND headers ${CMAKE_CURRENT_BINARY_DIR}/${header})
  endforeach()
  install(FILES ${headers} DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/openocean/messages)
  install(TARGETS openocean_messages EXPORT openocean_messages-cpp-targets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
endif()

if(OPENOCEAN_PYTHON)
  set(OPENOCEAN_PYTHON_DIR ${PROJECT_BINARY_DIR}/python)
  set(python_sources)
  foreach(proto IN LISTS OPENOCEAN_PROTOS)
    string(REGEX REPLACE "\\.proto$" "_pb2.py" python_source ${proto})
    list(APPEND python_sources ${OPENOCEAN_PYTHON_DIR}/${python_source})
  endforeach()
  add_custom_command(
    OUTPUT ${python_sources}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${OPENOCEAN_PYTHON_DIR}
    COMMAND protobuf::protoc --python_out=${OPENOCEAN_PYTHON_DIR}
            -I ${CMAKE_CURRENT_SOURCE_DIR} ${OPENOCEAN_PROTOS}
    DEPENDS ${OPENOCEAN_PROTOS}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Generating Python Protobuf modules"
    VERBATIM)
  add_custom_target(openocean_messages_python ALL DEPENDS ${python_sources})
  install(DIRECTORY ${OPENOCEAN_PYTHON_DIR}/openocean DESTINATION ${OPENOCEAN_INSTALL_PYTHON_DIR}
    PATTERN __pycache__ EXCLUDE)
endif()

if(OPENOCEAN_NANOPB)
  set(nanopb_dir ${PROJECT_BINARY_DIR}/nanopb)
  set(nanopb_options ${CMAKE_CURRENT_SOURCE_DIR}/openocean/messages/nanopb.options)
  set(nanopb_sources)
  foreach(proto IN LISTS OPENOCEAN_PROTOS)
    string(REGEX REPLACE "\\.proto$" ".pb" stem ${proto})
    list(APPEND nanopb_sources ${nanopb_dir}/${stem}.c ${nanopb_dir}/${stem}.h)
  endforeach()
  add_custom_command(
    OUTPUT ${nanopb_sources}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${nanopb_dir}
    COMMAND protobuf::protoc --plugin=protoc-gen-nanopb=${NANOPB_PROTOC_PLUGIN}
            "--nanopb_opt=-q -f ${nanopb_options}" --nanopb_out=${nanopb_dir}
            -I ${CMAKE_CURRENT_SOURCE_DIR} ${OPENOCEAN_PROTOS}
    DEPENDS ${OPENOCEAN_PROTOS} ${nanopb_options}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Generating nanopb C sources"
    VERBATIM)
  add_library(openocean_messages_nanopb ${nanopb_sources})
  set_target_properties(openocean_messages_nanopb PROPERTIES
    VERSION ${PROJECT_VERSION} SOVERSION ${OPENOCEAN_SOVERSION} EXPORT_NAME nanopb)
  # Its own directory, since the C++ headers have the same names
  set(nanopb_include_dir ${CMAKE_INSTALL_INCLUDEDIR}/openocean_messages_nanopb)
  target_include_directories(openocean_messages_nanopb PUBLIC
    $<BUILD_INTERFACE:${nanopb_dir}>
    $<INSTALL_INTERFACE:${nanopb_include_dir}>)
  target_link_libraries(openocean_messages_nanopb PUBLIC nanopb::protobuf-nanopb-static)

  install(DIRECTORY ${nanopb_dir}/openocean DESTINATION ${nanopb_include_dir}
    FILES_MATCHING PATTERN "*.h")
  install(TARGETS openocean_messages_nanopb EXPORT openocean_messages-nanopb-targets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
endif()

if(OPENOCEAN_LCM)
  include(${CMAKE_CURRENT_SOURCE_DIR}/generators/ProtobufGenerateLcm.cmake)
  set(converter)
  if(OPENOCEAN_CPP)
    set(converter
      CONVERTER_TARGET openocean_messages_lcm_convert
      HEADER openocean/lcm_convert.h
      LINK_LIBRARIES openocean_messages)
  endif()
  set(lcm_dir ${PROJECT_BINARY_DIR}/lcm)
  protobuf_generate_lcm(
    TARGET openocean_messages_lcm
    OUTPUT_DIR ${lcm_dir}
    PROTOS ${OPENOCEAN_PROTOS}
    IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR}
    ${converter})
  set_target_properties(openocean_messages_lcm PROPERTIES EXPORT_NAME lcm)
  target_include_directories(openocean_messages_lcm INTERFACE
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)

  install(DIRECTORY ${lcm_dir}/lcm-gen/openocean DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
  # For lcm-gen's other languages
  install(DIRECTORY ${lcm_dir}/protoc-gen-lcm/ DESTINATION ${CMAKE_INSTALL_DATADIR}/openocean_messages/lcm
    FILES_MATCHING PATTERN "*.lcm" PATTERN openocean EXCLUDE)
  set(lcm_targets openocean_messages_lcm)
  if(OPENOCEAN_CPP)
    set_target_properties(openocean_messages_lcm_convert PROPERTIES EXPORT_NAME lcm_convert)
    install(FILES ${lcm_dir}/protoc-gen-lcm/openocean/lcm_convert.h
      DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/openocean)
    list(APPEND lcm_targets openocean_messages_lcm_convert)
  endif()
  install(TARGETS ${lcm_targets} EXPORT openocean_messages-lcm-targets)
endif()

if(OPENOCEAN_RUST)
  add_custom_target(openocean_messages_rust ALL
    COMMAND ${OPENOCEAN_CARGO} build --manifest-path ${OPENOCEAN_CARGO_MANIFEST}
    USES_TERMINAL
    VERBATIM)
endif()

if(OPENOCEAN_ROS)
  include(${CMAKE_CURRENT_SOURCE_DIR}/generators/ProtobufGenerateRos.cmake)
  set(OPENOCEAN_ROS_DIR ${PROJECT_BINARY_DIR}/ros)
  set(OPENOCEAN_ROS_PACKAGE openocean_msgs)
  set(OPENOCEAN_ROS_CONVERT_PACKAGE openocean_msgs_convert)
  set(OPENOCEAN_ROS_OPTIONS
    version=${PROJECT_VERSION}
    soversion=${OPENOCEAN_SOVERSION}
    "maintainer=Toby Schneider"
    maintainer_email=toby@oceansoft.org
    license=Apache-2.0)
  protobuf_generate_ros(
    TARGET openocean_messages_ros
    PACKAGE ${OPENOCEAN_ROS_PACKAGE}
    OUTPUT_DIR ${OPENOCEAN_ROS_DIR}
    PROTOS ${OPENOCEAN_PROTOS}
    IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR}
    OPTIONS ${OPENOCEAN_ROS_OPTIONS}
    CONVERT_PACKAGE ${OPENOCEAN_ROS_CONVERT_PACKAGE})
endif()

if(BUILD_TESTING)
  add_subdirectory(test)
endif()
