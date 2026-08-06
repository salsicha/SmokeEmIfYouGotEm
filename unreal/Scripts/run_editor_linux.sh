#!/usr/bin/env bash
# Launch the Unreal editor for RaftSim on Linux hybrid-graphics machines.
# Usage: unreal/Scripts/run_editor_linux.sh [extra UnrealEditor args...]
#   e.g. unreal/Scripts/run_editor_linux.sh -game -windowed -resx=2560 -resy=1440
#        unreal/Scripts/run_editor_linux.sh /Game/RaftSim/Maps/L_Troublemaker -game
#
# Why the env pins: on Intel+NVIDIA laptops the interactive editor segfaulted
# inside the NVIDIA driver at swapchain AcquireImageIndex during present
# (unreal/Saved/Crashes 2026-08-06). The system exposes many Vulkan ICDs
# (nvidia, nouveau, intel, lavapipe, ...) and hybrid PRIME presentation is
# fragile when they all join surface negotiation. Restricting Vulkan to the
# proprietary NVIDIA ICD and pinning the Optimus layer makes the editor
# stable (verified 2026-08-06: full init + sustained presenting, no crash).
# Headless flows (-nullrhi / -RenderOffscreen) never hit this path and do
# not need this script.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UE_ROOT="${UE_ROOT:-$HOME/UnrealEngine}"
NVIDIA_ICD="${NVIDIA_ICD:-/usr/share/vulkan/icd.d/nvidia_icd.json}"

if [[ ! -f "$NVIDIA_ICD" ]]; then
  echo "warning: $NVIDIA_ICD not found; launching without the ICD pin" >&2
  exec env __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia \
    "$UE_ROOT/Engine/Binaries/Linux/UnrealEditor" \
    "$REPO_ROOT/unreal/SmokeEmIfYouGotEm.uproject" -nop4 "$@"
fi

exec env \
  VK_DRIVER_FILES="$NVIDIA_ICD" \
  __NV_PRIME_RENDER_OFFLOAD=1 \
  __VK_LAYER_NV_optimus=NVIDIA_only \
  __GLX_VENDOR_LIBRARY_NAME=nvidia \
  "$UE_ROOT/Engine/Binaries/Linux/UnrealEditor" \
  "$REPO_ROOT/unreal/SmokeEmIfYouGotEm.uproject" -nop4 "$@"
