#!/usr/bin/env bash
# Installs the build dependencies on Ubuntu.
#
# Usage: init.sh [--ros]
#   --ros  also install what's needed to build the generated ROS 2 package
#          (needs the ROS 2 apt repository: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
set -euo pipefail

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    SUDO=sudo
fi

packages=(
    cmake
    ninja-build
    g++
    pkg-config
    libprotobuf-dev
    protobuf-compiler
    libudunits2-dev
    python3
    python3-protobuf
)

if [ "${1:-}" = "--ros" ]; then
    ROS_DISTRO=${ROS_DISTRO:-jazzy}
    packages+=(
        "ros-${ROS_DISTRO}-ament-cmake"
        "ros-${ROS_DISTRO}-rosidl-default-generators"
        "ros-${ROS_DISTRO}-rosidl-default-runtime"
        "ros-${ROS_DISTRO}-builtin-interfaces"
        python3-colcon-common-extensions
    )
fi

$SUDO apt-get update
$SUDO apt-get install -y --no-install-recommends "${packages[@]}"
