#!/usr/bin/env bash
# Adds the ROS 2 apt repository with the ros2-apt-source package, as in
# https://docs.ros.org/en/rolling/Installation/Ubuntu-Install-Debs.html
set -euo pipefail

# shellcheck source=../../versions.env
. "$(dirname "$0")/../../versions.env"

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ca-certificates curl

version=${ROS_APT_SOURCE_VERSION}
codename=$(. /etc/os-release && echo "${VERSION_CODENAME}")

curl -fsSL -o /tmp/ros2-apt-source.deb \
    "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${version}/ros2-apt-source_${version}.${codename}_all.deb"
apt-get install -y /tmp/ros2-apt-source.deb
