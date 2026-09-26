#!/usr/bin/env bash
# Fails if the protos changed incompatibly (buf breaking) between BASE and the working tree,
# unless the version's compatibility component was bumped: the major version, or in 0.y.z the
# minor (and in 0.0.z the patch), as Cargo treats versions.
#
# Usage: check-buf.sh BASE   (a git revision, e.g. origin/main; BUF overrides the buf binary)
set -euo pipefail

base=$1
buf=${BUF:-buf}
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

if ! git cat-file -e "${base}:src/openocean/messages" 2>/dev/null; then
    echo "${base} has no protos to compare against"
    exit 0
fi

version() { sed -n 's/^project(openocean_messages VERSION \([0-9.]*\).*/\1/p'; }
compatibility() {
    local major minor patch
    IFS=. read -r major minor patch <<< "$1"
    if [ "${major}" != 0 ]; then echo "${major}"
    elif [ "${minor}" != 0 ]; then echo "0.${minor}"
    else echo "0.0.${patch}"
    fi
}
base_version=$(git show "${base}:CMakeLists.txt" | version)
head_version=$(version < CMakeLists.txt)

if "${buf}" breaking --against ".git#ref=$(git rev-parse "${base}")" --against-config buf.yaml; then
    echo "No breaking changes since ${base}"
    exit 0
fi
if [ -n "${base_version}" ] && [ "$(compatibility "${base_version}")" != "$(compatibility "${head_version}")" ]; then
    echo "Breaking changes allowed by the version bump ${base_version} -> ${head_version}"
    exit 0
fi
echo "Breaking changes need a bump of the version in CMakeLists.txt (${base_version:-none} -> ${head_version}):" \
    "the major version, or in 0.y.z the minor"
exit 1
