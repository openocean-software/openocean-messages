#!/usr/bin/env bash
# Installs the Ubuntu dependencies for the selected outputs, and writes init.cmake so
# that new build directories enable the same outputs by default.
#
# Usage: init.sh [--cxx] [--python] [--ros] [--nanopb] [--rust]   (default: --cxx)
#   --cxx     C++ Protobuf library (and its UDUNITS-2 units test)
#   --python  Python Protobuf modules
#   --ros     ROS 2 message package, built with colcon. Needs the ROS 2 apt repository:
#             https://docs.ros.org/en/rolling/Installation/Ubuntu-Install-Debs.html
#             ROS_DISTRO defaults to jazzy on Ubuntu 24.04 and lyrical on 26.04
#   --nanopb  nanopb C library
#   --rust    Rust crate (prost), built with cargo
set -euo pipefail

cd "$(dirname "$0")"

cxx=OFF
python=OFF
ros=OFF
nanopb=OFF
rust=OFF
[ $# -eq 0 ] && cxx=ON
for arg in "$@"; do
    case "${arg}" in
        --cxx) cxx=ON ;;
        --python) python=ON ;;
        --ros) ros=ON ;;
        --nanopb) nanopb=ON ;;
        --rust) rust=ON ;;
        -h | --help)
            sed -n '5,13s/^# \{0,1\}//p' "$0"
            exit 0
            ;;
        *)
            sed -n '5,13s/^# \{0,1\}//p' "$0" >&2
            exit 1
            ;;
    esac
done

packages=(cmake ninja-build protobuf-compiler)
if [ "${cxx}" = ON ]; then
    packages+=(g++ libprotobuf-dev pkg-config libudunits2-dev)
fi
if [ "${python}" = ON ] || [ "${ros}" = ON ]; then
    packages+=(python3 python3-protobuf)
fi
if [ "${ros}" = ON ]; then
    if [ -z "${ROS_DISTRO:-}" ]; then
        case "$(. /etc/os-release && echo "${VERSION_CODENAME}")" in
            noble) ROS_DISTRO=jazzy ;;
            resolute) ROS_DISTRO=lyrical ;;
            *)
                echo "Set ROS_DISTRO for this Ubuntu release" >&2
                exit 1
                ;;
        esac
    fi
    packages+=(
        g++
        "ros-${ROS_DISTRO}-ament-cmake"
        "ros-${ROS_DISTRO}-rosidl-default-generators"
        "ros-${ROS_DISTRO}-rosidl-default-runtime"
        "ros-${ROS_DISTRO}-builtin-interfaces"
        python3-colcon-common-extensions
    )
fi
if [ "${nanopb}" = ON ]; then
    packages+=(gcc nanopb libnanopb-dev)
fi
if [ "${rust}" = ON ]; then
    packages+=(cargo)
fi

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    SUDO=sudo
fi
$SUDO apt-get update
$SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${packages[@]}"

cat > init.cmake <<EOF
# Written by init.sh
set(OPENOCEAN_CPP_DEFAULT ${cxx})
set(OPENOCEAN_PYTHON_DEFAULT ${python})
set(OPENOCEAN_ROS_DEFAULT ${ros})
set(OPENOCEAN_NANOPB_DEFAULT ${nanopb})
set(OPENOCEAN_RUST_DEFAULT ${rust})
EOF
echo "Wrote init.cmake: OPENOCEAN_CPP=${cxx} OPENOCEAN_PYTHON=${python} OPENOCEAN_ROS=${ros} OPENOCEAN_NANOPB=${nanopb} OPENOCEAN_RUST=${rust}"
