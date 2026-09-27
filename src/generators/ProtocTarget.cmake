# Defines protobuf::protoc unless find_package(Protobuf) already has. FindProtobuf needs a compiler
# and the Protobuf headers, but generating non-C++ outputs only needs protoc.
if(NOT TARGET protobuf::protoc)
  find_program(Protobuf_PROTOC_EXECUTABLE protoc)
  if(NOT Protobuf_PROTOC_EXECUTABLE)
    message(FATAL_ERROR "protoc not found")
  endif()
  add_executable(protobuf::protoc IMPORTED)
  set_target_properties(protobuf::protoc PROPERTIES IMPORTED_LOCATION ${Protobuf_PROTOC_EXECUTABLE})
endif()
