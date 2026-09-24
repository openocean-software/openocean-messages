#!/usr/bin/env bash
set -euo pipefail

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    SUDO=sudo
fi

$SUDO apt-get update
$SUDO apt-get install -y --no-install-recommends \
    cmake \
    ninja-build \
    g++ \
    pkg-config \
    libprotobuf-dev \
    protobuf-compiler \
    libudunits2-dev
