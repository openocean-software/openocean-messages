#!/usr/bin/env bash
# Builds the generated ROS 2 packages and openocean_msgs_check with colcon, then
# checks the messages from C++ and Python, and the converters to and from Protobuf.
#
# Usage: build_and_check.sh WORK_DIR PYTHON PACKAGES_DIR...
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
for check in check_messages check_convert check_convert_mapping; do
    "${work}/install/openocean_msgs_check/lib/openocean_msgs_check/${check}"
done
"${python}" "${here}/check_messages.py"
