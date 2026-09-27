# Runs lcm-gen on every .lcm file in TYPES_DIR, writing C++ headers to CPP_DIR, then touches STAMP
file(GLOB types ${TYPES_DIR}/*.lcm)
file(REMOVE_RECURSE ${CPP_DIR})
execute_process(COMMAND ${LCM_GEN} --cpp --cpp-std=c++11 --cpp-hpath ${CPP_DIR} ${types} RESULT_VARIABLE result)
if(NOT result EQUAL 0)
  message(FATAL_ERROR "lcm-gen failed")
endif()
file(TOUCH ${STAMP})
