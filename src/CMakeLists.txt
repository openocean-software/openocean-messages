set(OPENOCEAN_PROTOS
  openocean/messages/options.proto
  openocean/messages/common.proto
  openocean/messages/navigation.proto
  openocean/messages/control.proto)

if(OPENOCEAN_CPP)
  add_library(openocean_messages)
  protobuf_generate(
    TARGET openocean_messages
    LANGUAGE cpp
    PROTOS ${OPENOCEAN_PROTOS}
    IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR}
    PROTOC_OUT_DIR ${CMAKE_CURRENT_BINARY_DIR})
  target_include_directories(openocean_messages PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}>)
  target_link_libraries(openocean_messages PUBLIC protobuf::libprotobuf)
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
endif()

if(OPENOCEAN_ROS)
  include(${CMAKE_CURRENT_SOURCE_DIR}/generators/ProtobufGenerateRos.cmake)
  set(OPENOCEAN_ROS_DIR ${PROJECT_BINARY_DIR}/ros)
  set(OPENOCEAN_ROS_PACKAGE openocean_msgs)
  set(OPENOCEAN_ROS_OPTIONS
    "maintainer=Toby Schneider"
    maintainer_email=toby@oceansoft.org
    license=Apache-2.0)
  protobuf_generate_ros(
    TARGET openocean_messages_ros
    PACKAGE ${OPENOCEAN_ROS_PACKAGE}
    OUTPUT_DIR ${OPENOCEAN_ROS_DIR}
    PROTOS ${OPENOCEAN_PROTOS}
    IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR}
    OPTIONS ${OPENOCEAN_ROS_OPTIONS})
endif()

if(BUILD_TESTING)
  add_subdirectory(test)
endif()
