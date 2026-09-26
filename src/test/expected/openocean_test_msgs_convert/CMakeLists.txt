cmake_minimum_required(VERSION 3.10)
project(openocean_test_msgs_convert VERSION 0.1.0 LANGUAGES CXX)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)
find_package(openocean_test_msgs REQUIRED)
find_package(Protobuf REQUIRED)
find_package(openocean_msgs_convert REQUIRED)

set(protos
    mapping.proto
)

option(BUILD_SHARED_LIBS "Build shared libraries" ON)
add_library(${PROJECT_NAME})
set_target_properties(${PROJECT_NAME} PROPERTIES
  VERSION ${PROJECT_VERSION} SOVERSION 1)
protobuf_generate(
  TARGET ${PROJECT_NAME}
  LANGUAGE cpp
  PROTOS ${protos}
  IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR} ${openocean_msgs_convert_PROTO_DIR}
  PROTOC_OUT_DIR ${CMAKE_CURRENT_BINARY_DIR})
target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}>
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include/${PROJECT_NAME}>)
target_link_libraries(${PROJECT_NAME} PUBLIC
  protobuf::libprotobuf ${openocean_test_msgs_TARGETS} openocean_msgs_convert::openocean_msgs_convert)

install(DIRECTORY include/ DESTINATION include/${PROJECT_NAME})
install(DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/ DESTINATION include/${PROJECT_NAME}
  FILES_MATCHING PATTERN "*.pb.h" PATTERN "CMakeFiles" EXCLUDE)
install(TARGETS ${PROJECT_NAME} EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib LIBRARY DESTINATION lib)
# So converter packages for protos that import these can build against them (<package>_PROTO_DIR)
foreach(proto IN LISTS protos)
  get_filename_component(directory ${proto} DIRECTORY)
  install(FILES ${proto} DESTINATION share/${PROJECT_NAME}/proto/${directory})
endforeach()

ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)
ament_export_dependencies(openocean_test_msgs Protobuf openocean_msgs_convert)
ament_package(CONFIG_EXTRAS cmake/${PROJECT_NAME}-extras.cmake)
