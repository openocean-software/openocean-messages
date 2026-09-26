#!/usr/bin/env bash
# Fails if a shared library's ABI changed incompatibly (abidiff) between BASE and the working
# tree, unless OPENOCEAN_SOVERSION was bumped.
#
# Usage: check-abi.sh BASE   (a git revision, e.g. origin/main)
set -euo pipefail

base=$1
here=$(cd "$(dirname "$0")" && pwd)
root=$(git -C "${here}" rev-parse --show-toplevel)
cd "${root}"

soversion() { sed -n 's/^set(OPENOCEAN_SOVERSION \([0-9]*\))$/\1/p'; }
base_soversion=$( (git show "${base}:CMakeLists.txt" 2>/dev/null || true) | soversion)
head_soversion=$(soversion < CMakeLists.txt)
if [ -z "${base_soversion}" ]; then
    echo "${base} has no OPENOCEAN_SOVERSION, so no shared libraries to compare"
    exit 0
fi

work=$(mktemp -d)
trap 'git worktree remove --force "${work}/base" 2>/dev/null || true; rm -rf "${work}"' EXIT
git worktree add --quiet --detach "${work}/base" "${base}"

build() {
    cmake -S "$1" -B "$2" -G Ninja -DCMAKE_BUILD_TYPE=Debug -DBUILD_SHARED_LIBS=ON \
        -DBUILD_TESTING=OFF -DOPENOCEAN_CPP=ON -DOPENOCEAN_NANOPB=ON -DOPENOCEAN_PYTHON=OFF \
        -DOPENOCEAN_ROS=OFF -DOPENOCEAN_RUST=OFF -DOPENOCEAN_LCM=OFF > "$2.log" 2>&1
    ninja -C "$2" >> "$2.log" 2>&1
}
build "${work}/base" "${work}/base-build"
build "${root}" "${work}/head-build"

incompatible=()
for library in libopenocean_messages.so libopenocean_messages_nanopb.so; do
    old="${work}/base-build/src/${library}"
    new="${work}/head-build/src/${library}"
    if [ ! -e "${old}" ] || [ ! -e "${new}" ]; then
        echo "${library}: not built on both sides, skipped"
        continue
    fi
    status=0
    abidiff --no-added-syms --suppressions "${here}/abi.suppr" "${old}" "${new}" \
        > "${work}/${library}.abidiff" || status=$?
    # abidiff's exit status is a bit field: 1 error, 2 usage error, 4 ABI change, 8 incompatible.
    # With added symbols left out, any change is breaking: abidiff only calls removals incompatible,
    # but a generated class growing a field breaks every caller that inlines its accessors.
    if (( status & 3 )); then
        cat "${work}/${library}.abidiff"
        echo "${library}: abidiff failed"
        exit 1
    elif (( status & 12 )); then
        cat "${work}/${library}.abidiff"
        echo "${library}: incompatible ABI change"
        incompatible+=("${library}")
    else
        echo "${library}: no ABI change, or only additions"
    fi
done

if (( ${#incompatible[@]} )) && [ "${base_soversion}" = "${head_soversion}" ]; then
    echo "The ABI of ${incompatible[*]} changed incompatibly, but OPENOCEAN_SOVERSION is still" \
        "${head_soversion}: bump it in CMakeLists.txt"
    exit 1
fi
echo "ABI check passed (OPENOCEAN_SOVERSION ${base_soversion} -> ${head_soversion})"
