#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
BUILD_DIR=${BUILD_DIR:-build}

cmake -S . -B "${BUILD_DIR}" -G Ninja "$@"
ninja -C "${BUILD_DIR}"
