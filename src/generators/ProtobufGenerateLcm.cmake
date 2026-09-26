set(PROTOC_GEN_LCM ${CMAKE_CURRENT_LIST_DIR}/protoc-gen-lcm)
set(PROTOC_GEN_LCM_GENERATE ${CMAKE_CURRENT_LIST_DIR}/GenerateLcm.cmake)
file(GLOB PROTOC_GEN_LCM_SOURCES ${CMAKE_CURRENT_LIST_DIR}/openocean_gen/*.py)

# protobuf_generate_lcm(TARGET <interface library> OUTPUT_DIR <dir> HEADER <path>
#                       PROTOS <files>... IMPORT_DIRS <dirs>... LINK_LIBRARIES <proto library>)
#
# Generates LCM types from PROTOS into <OUTPUT_DIR>/protoc-gen-lcm, their C++ types with lcm-gen
# into <OUTPUT_DIR>/lcm-gen, and the converter header HEADER (e.g. openocean/lcm_convert.h).
# TARGET is an interface library for them, linked to the Protobuf C++ library.
function(protobuf_generate_lcm)
  cmake_parse_arguments(arg "" "TARGET;OUTPUT_DIR;HEADER" "PROTOS;IMPORT_DIRS;LINK_LIBRARIES" ${ARGN})

  set(types_dir ${arg_OUTPUT_DIR}/protoc-gen-lcm)
  set(cpp_dir ${arg_OUTPUT_DIR}/lcm-gen)
  set(include_args)
  foreach(dir IN LISTS arg_IMPORT_DIRS)
    get_filename_component(dir ${dir} ABSOLUTE)
    list(APPEND include_args -I ${dir})
  endforeach()
  set(protos)
  foreach(proto IN LISTS arg_PROTOS)
    get_filename_component(proto ${proto} ABSOLUTE)
    list(APPEND protos ${proto})
  endforeach()

  # Removing the outputs first drops files for deleted messages
  add_custom_command(
    OUTPUT ${types_dir}/${arg_HEADER}
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${types_dir}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${types_dir}
    COMMAND protobuf::protoc --plugin=protoc-gen-lcm=${PROTOC_GEN_LCM}
            --lcm_out=header=${arg_HEADER}:${types_dir} ${include_args} ${protos}
    COMMAND ${CMAKE_COMMAND} -DLCM_GEN=${LCM_GEN} -DTYPES_DIR=${types_dir} -DCPP_DIR=${cpp_dir}
            -P ${PROTOC_GEN_LCM_GENERATE}
    DEPENDS ${protos} ${PROTOC_GEN_LCM} ${PROTOC_GEN_LCM_SOURCES} ${PROTOC_GEN_LCM_GENERATE}
    COMMENT "Generating LCM types and converters in ${arg_OUTPUT_DIR}"
    VERBATIM)
  add_custom_target(${arg_TARGET}_generate DEPENDS ${types_dir}/${arg_HEADER})

  add_library(${arg_TARGET} INTERFACE)
  add_dependencies(${arg_TARGET} ${arg_TARGET}_generate)
  target_include_directories(${arg_TARGET} INTERFACE
    $<BUILD_INTERFACE:${types_dir}> $<BUILD_INTERFACE:${cpp_dir}> ${LCM_INCLUDE_DIR})
  target_link_libraries(${arg_TARGET} INTERFACE ${arg_LINK_LIBRARIES})
endfunction()
