add_library(openocean_messages)
protobuf_generate(
  TARGET openocean_messages
  LANGUAGE cpp
  PROTOS
    openocean/options.proto
    openocean/navigation.proto
    openocean/control.proto
  IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR}
  PROTOC_OUT_DIR ${CMAKE_CURRENT_BINARY_DIR})
target_include_directories(openocean_messages PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}>)
target_link_libraries(openocean_messages PUBLIC protobuf::libprotobuf)
