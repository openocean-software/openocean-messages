add_executable(check_units check_units.cpp)
target_link_libraries(check_units PRIVATE openocean_messages PkgConfig::UDUNITS)
add_test(NAME check_units COMMAND check_units)
