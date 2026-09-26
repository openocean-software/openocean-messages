#!/usr/bin/env bash
# Adds the ROS 2 apt repository with the ros2-apt-source package, as in
# https://docs.ros.org/en/rolling/Installation/Ubuntu-Install-Debs.html
set -euo pipefail

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ca-certificates curl

auth=()
if [ -n "${GH_TOKEN:-}" ]; then
    auth=(-H "Authorization: Bearer ${GH_TOKEN}")
fi
version=$(curl -fsSL "${auth[@]}" https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest |
    sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p')
codename=$(. /etc/os-release && echo "${VERSION_CODENAME}")

curl -fsSL -o /tmp/ros2-apt-source.deb \
    "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${version}/ros2-apt-source_${version}.${codename}_all.deb"
apt-get install -y /tmp/ros2-apt-source.deb
