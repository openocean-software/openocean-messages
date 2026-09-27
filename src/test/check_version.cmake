# Checks that the Rust crate's version matches the project's, since Cargo.toml can't read it
file(READ ${CARGO_TOML} cargo_toml)
if(NOT cargo_toml MATCHES "\nversion = \"([^\"]+)\"")
  message(FATAL_ERROR "No version in ${CARGO_TOML}")
endif()
if(NOT CMAKE_MATCH_1 STREQUAL PROJECT_VERSION)
  message(FATAL_ERROR "${CARGO_TOML} has version ${CMAKE_MATCH_1}, but the project is ${PROJECT_VERSION}")
endif()
