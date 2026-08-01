#!/usr/bin/env bash
# Package a Linux build of RaftSim (release-1.0-plan.md P1/P6).
# Usage: unreal/Scripts/package_linux.sh [Development|Shipping] [output-dir]
# Set UE_ROOT to your engine location (default: ~/UnrealEngine source build).
# Build physics/cpp/build-ue/libraftsim_water.a first via
# unreal/Scripts/build_solver_lib.sh so the packaged game ships the live solver.
set -euo pipefail

CONFIG="${1:-Development}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUTPUT_DIR="${2:-$REPO_ROOT/unreal/Packaged/Linux-$CONFIG}"
UE_ROOT="${UE_ROOT:-$HOME/UnrealEngine}"

"$UE_ROOT/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun \
  -project="$REPO_ROOT/unreal/SmokeEmIfYouGotEm.uproject" \
  -platform=Linux -clientconfig="$CONFIG" \
  -build -cook -stage -pak -package \
  -archive -archivedirectory="$OUTPUT_DIR" \
  -nop4 -utf8output -unattended

echo "Packaged: $OUTPUT_DIR"
