set(PROTOC_GEN_ROS ${CMAKE_CURRENT_LIST_DIR}/protoc-gen-ros)
file(GLOB PROTOC_GEN_ROS_SOURCES ${CMAKE_CURRENT_LIST_DIR}/openocean_gen/*.py)

# protobuf_generate_ros(TARGET <target> PACKAGE <ros_package> OUTPUT_DIR <dir>
#                       PROTOS <files>... IMPORT_DIRS <dirs>... [OPTIONS <key=value>...])
#
# Generates the ROS 2 interface package <OUTPUT_DIR>/<PACKAGE> from PROTOS (relative to
# CMAKE_CURRENT_SOURCE_DIR). OPTIONS are passed to protoc-gen-ros.
function(protobuf_generate_ros)
  cmake_parse_arguments(arg "" "TARGET;PACKAGE;OUTPUT_DIR" "PROTOS;IMPORT_DIRS;OPTIONS" ${ARGN})

  set(out ${arg_OUTPUT_DIR}/${arg_PACKAGE})
  set(parameter "package=${arg_PACKAGE}")
  foreach(option IN LISTS arg_OPTIONS)
    string(APPEND parameter ",${option}")
  endforeach()
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

  # Removing the package first drops .msg files for deleted messages
  add_custom_command(
    OUTPUT ${out}/package.xml
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${out}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${out}
    COMMAND protobuf::protoc --plugin=protoc-gen-ros=${PROTOC_GEN_ROS}
            --ros_out=${parameter}:${out} ${include_args} ${protos}
    DEPENDS ${protos} ${PROTOC_GEN_ROS} ${PROTOC_GEN_ROS_SOURCES}
    COMMENT "Generating ROS 2 package ${arg_PACKAGE}"
    VERBATIM)
  add_custom_target(${arg_TARGET} ALL DEPENDS ${out}/package.xml)
endfunction()
