#!/bin/zsh
# Build the raftsim_water static library for linking into the RaftSimWater
# module (release-1.0-plan.md §5 A-1). Output: physics/cpp/build-ue/libraftsim_water.a
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD_DIR="$REPO_ROOT/physics/cpp/build-ue"

cmake -S "$REPO_ROOT/physics/cpp" -B "$BUILD_DIR" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DCMAKE_CXX_VISIBILITY_PRESET=hidden
cmake --build "$BUILD_DIR" --target raftsim_water -j

echo "Built: $BUILD_DIR/libraftsim_water.a"
