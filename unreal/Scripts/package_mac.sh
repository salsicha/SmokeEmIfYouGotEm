#!/bin/zsh
# Package a macOS build of RaftSim (release-1.0-plan.md P1/P6).
# Usage: unreal/Scripts/package_mac.sh [Development|Shipping] [output-dir]
set -euo pipefail

CONFIG="${1:-Development}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUTPUT_DIR="${2:-$REPO_ROOT/unreal/Packaged/Mac-$CONFIG}"
UE_ROOT="/Users/Shared/Epic Games/UE_5.8"
ZAMBEZI_MAP="$REPO_ROOT/unreal/Content/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_ZambeziBatokaGorge_PhysicalCorridorCandidate.umap"

if [[ ! -f "$ZAMBEZI_MAP" ]]; then
  "$UE_ROOT/Engine/Build/BatchFiles/Mac/Build.sh" \
    SmokeEmIfYouGotEmEditor Mac Development \
    "$REPO_ROOT/unreal/SmokeEmIfYouGotEm.uproject" \
    -WaitMutex -NoHotReload
  "$UE_ROOT/Engine/Binaries/Mac/UnrealEditor-Cmd" \
    "$REPO_ROOT/unreal/SmokeEmIfYouGotEm.uproject" \
    -unattended -nop4 -nosplash -NoSound -RenderOffscreen \
    -RaftSimCreateLandscapeImportCandidateMaps \
    -RaftSimLandscapeImportCandidateRiverId=zambezi_batoka_gorge \
    -RaftSimExitAfterEnvironmentAutomation
fi

if [[ ! -f "$ZAMBEZI_MAP" ]]; then
  echo "Zambezi runnable map generation failed: $ZAMBEZI_MAP" >&2
  exit 18
fi

"$UE_ROOT/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun \
  -project="$REPO_ROOT/unreal/SmokeEmIfYouGotEm.uproject" \
  -platform=Mac -clientconfig="$CONFIG" \
  -build -cook -stage -pak -package \
  -archive -archivedirectory="$OUTPUT_DIR" \
  -nop4 -utf8output -unattended

echo "Packaged: $OUTPUT_DIR"
