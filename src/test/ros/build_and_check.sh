#!/usr/bin/env bash
# Builds the generated ROS 2 packages and openocean_msgs_check with colcon, then
# checks the messages from C++ and Python.
#
# Usage: build_and_check.sh WORK_DIR PYTHON PACKAGE_DIR...
set -eo pipefail

work=$1
python=$2
shift 2
here=$(cd "$(dirname "$0")" && pwd)

colcon --log-base "${work}/log" build \
    --base-paths "$@" "${here}/openocean_msgs_check" \
    --build-base "${work}/build" --install-base "${work}/install" \
    --event-handlers console_cohesion+ \
    --cmake-args -DPython3_EXECUTABLE="${python}" -DBUILD_TESTING=OFF

# shellcheck disable=SC1091
source "${work}/install/setup.bash"
"${work}/install/openocean_msgs_check/lib/openocean_msgs_check/check_messages"
"${python}" "${here}/check_messages.py"
