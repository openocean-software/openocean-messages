set(PROTOC_GEN_ROS ${CMAKE_CURRENT_LIST_DIR}/protoc-gen-ros)
file(GLOB PROTOC_GEN_ROS_SOURCES ${CMAKE_CURRENT_LIST_DIR}/openocean_gen/*.py)

# protobuf_generate_ros(TARGET <target> PACKAGE <ros_package> OUTPUT_DIR <dir>
#                       PROTOS <files>... IMPORT_DIRS <dirs>... [OPTIONS <key=value>...]
#                       [CONVERT_PACKAGE <ros_package> [CONVERT_PROTOS <files>...]])
#
# Generates the ROS 2 interface package <OUTPUT_DIR>/<PACKAGE> from PROTOS (relative to
# CMAKE_CURRENT_SOURCE_DIR). With CONVERT_PACKAGE, also generates <OUTPUT_DIR>/<CONVERT_PACKAGE>,
# which builds the Protobuf C++ library from CONVERT_PROTOS (default PROTOS; they must include
# every non-Protobuf import) and converts to and from PACKAGE. OPTIONS are passed to protoc-gen-ros.
function(protobuf_generate_ros)
  cmake_parse_arguments(arg "" "TARGET;PACKAGE;OUTPUT_DIR;CONVERT_PACKAGE"
                        "PROTOS;IMPORT_DIRS;OPTIONS;CONVERT_PROTOS" ${ARGN})

  set(parameter "package=${arg_PACKAGE}")
  foreach(option IN LISTS arg_OPTIONS)
    string(APPEND parameter ",${option}")
  endforeach()
  set(include_args)
  set(import_dirs)
  foreach(dir IN LISTS arg_IMPORT_DIRS)
    get_filename_component(dir ${dir} ABSOLUTE)
    list(APPEND include_args -I ${dir})
    list(APPEND import_dirs ${dir})
  endforeach()
  set(protos)
  foreach(proto IN LISTS arg_PROTOS)
    get_filename_component(proto ${proto} ABSOLUTE)
    list(APPEND protos ${proto})
  endforeach()

  set(packages ${arg_PACKAGE})
  set(outputs ${arg_OUTPUT_DIR}/${arg_PACKAGE}/package.xml)
  set(copy_protos)
  set(convert_protos)
  if(arg_CONVERT_PACKAGE)
    string(APPEND parameter ",convert_package=${arg_CONVERT_PACKAGE}")
    list(APPEND packages ${arg_CONVERT_PACKAGE})
    list(APPEND outputs ${arg_OUTPUT_DIR}/${arg_CONVERT_PACKAGE}/package.xml)
    if(NOT arg_CONVERT_PROTOS)
      set(arg_CONVERT_PROTOS ${arg_PROTOS})
    endif()
    # Copied to their import paths, which is where the package's protobuf_generate() expects them
    foreach(proto IN LISTS arg_CONVERT_PROTOS)
      get_filename_component(proto ${proto} ABSOLUTE)
      list(APPEND convert_protos ${proto})
      set(relative)
      foreach(dir IN LISTS import_dirs)
        file(RELATIVE_PATH candidate ${dir} ${proto})
        if(NOT candidate MATCHES "^\\.\\./")
          set(relative ${candidate})
          break()
        endif()
      endforeach()
      if(NOT relative)
        message(FATAL_ERROR "${proto} is not in any of IMPORT_DIRS")
      endif()
      set(destination ${arg_OUTPUT_DIR}/${arg_CONVERT_PACKAGE}/${relative})
      get_filename_component(destination_dir ${destination} DIRECTORY)
      list(APPEND copy_protos
        COMMAND ${CMAKE_COMMAND} -E make_directory ${destination_dir}
        COMMAND ${CMAKE_COMMAND} -E copy ${proto} ${destination})
    endforeach()
  endif()

  set(remove)
  foreach(package IN LISTS packages)
    list(APPEND remove COMMAND ${CMAKE_COMMAND} -E remove_directory ${arg_OUTPUT_DIR}/${package})
  endforeach()

  # Removing the packages first drops files for deleted messages
  add_custom_command(
    OUTPUT ${outputs}
    ${remove}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${arg_OUTPUT_DIR}
    COMMAND protobuf::protoc --plugin=protoc-gen-ros=${PROTOC_GEN_ROS}
            --ros_out=${parameter}:${arg_OUTPUT_DIR} ${include_args} ${protos}
    ${copy_protos}
    DEPENDS ${protos} ${convert_protos} ${PROTOC_GEN_ROS} ${PROTOC_GEN_ROS_SOURCES}
    COMMENT "Generating ROS 2 packages ${packages}"
    VERBATIM)
  add_custom_target(${arg_TARGET} ALL DEPENDS ${outputs})
endfunction()
