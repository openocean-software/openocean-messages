set(PROTOC_GEN_LCM ${CMAKE_CURRENT_LIST_DIR}/protoc-gen-lcm)
set(PROTOC_GEN_LCM_GENERATE ${CMAKE_CURRENT_LIST_DIR}/GenerateLcm.cmake)
file(GLOB PROTOC_GEN_LCM_SOURCES ${CMAKE_CURRENT_LIST_DIR}/openocean_gen/*.py)

# protobuf_generate_lcm(TARGET <library> OUTPUT_DIR <dir> PROTOS <files>... IMPORT_DIRS <dirs>...
#                       [CONVERTER_TARGET <library> HEADER <path> LINK_LIBRARIES <libraries>...])
#
# Generates LCM types from PROTOS into <OUTPUT_DIR>/protoc-gen-lcm, and their C++ types with lcm-gen
# into <OUTPUT_DIR>/lcm-gen, as the interface library TARGET. With CONVERTER_TARGET, also generates
# the converter header HEADER (e.g. openocean/lcm_convert.h) as that interface library, linked to
# TARGET and LINK_LIBRARIES (the Protobuf C++ library).
function(protobuf_generate_lcm)
  cmake_parse_arguments(arg "" "TARGET;OUTPUT_DIR;CONVERTER_TARGET;HEADER"
                        "PROTOS;IMPORT_DIRS;LINK_LIBRARIES" ${ARGN})

  set(types_dir ${arg_OUTPUT_DIR}/protoc-gen-lcm)
  set(cpp_dir ${arg_OUTPUT_DIR}/lcm-gen)
  set(stamp ${arg_OUTPUT_DIR}/lcm.stamp)
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
  set(parameter)
  if(arg_CONVERTER_TARGET)
    set(parameter header=${arg_HEADER}:)
  endif()

  # Removing the outputs first drops files for deleted messages
  add_custom_command(
    OUTPUT ${stamp}
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${types_dir}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${types_dir}
    COMMAND protobuf::protoc --plugin=protoc-gen-lcm=${PROTOC_GEN_LCM}
            --lcm_out=${parameter}${types_dir} ${include_args} ${protos}
    COMMAND ${CMAKE_COMMAND} -DLCM_GEN=${LCM_GEN} -DTYPES_DIR=${types_dir} -DCPP_DIR=${cpp_dir}
            -DSTAMP=${stamp} -P ${PROTOC_GEN_LCM_GENERATE}
    DEPENDS ${protos} ${PROTOC_GEN_LCM} ${PROTOC_GEN_LCM_SOURCES} ${PROTOC_GEN_LCM_GENERATE}
    COMMENT "Generating LCM types in ${arg_OUTPUT_DIR}"
    VERBATIM)
  add_custom_target(${arg_TARGET}_generate DEPENDS ${stamp})

  add_library(${arg_TARGET} INTERFACE)
  add_dependencies(${arg_TARGET} ${arg_TARGET}_generate)
  target_include_directories(${arg_TARGET} INTERFACE $<BUILD_INTERFACE:${cpp_dir}> ${LCM_INCLUDE_DIR})

  if(arg_CONVERTER_TARGET)
    add_library(${arg_CONVERTER_TARGET} INTERFACE)
    target_include_directories(${arg_CONVERTER_TARGET} INTERFACE $<BUILD_INTERFACE:${types_dir}>)
    target_link_libraries(${arg_CONVERTER_TARGET} INTERFACE ${arg_TARGET} ${arg_LINK_LIBRARIES})
  endif()
endfunction()
