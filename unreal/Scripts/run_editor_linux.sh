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
# Apply the Vulkan workarounds required by this driver/UE combination:
# disable async compute to avoid Xid 109 context-switch timeouts, force FIFO
# presentation, and serialize RHI work onto the render thread. The recorded
# NVIDIA crashes occurred on the dedicated RHI thread while WaitForFence ran
# after an outdated swapchain was recreated.
# Headless flows (-nullrhi / -RenderOffscreen) never hit this path and do
# not need this script.
# 2026-08-12: recurring VK_ERROR_DEVICE_LOST during the first Slate presents
# (no kernel Xid, no validation-layer errors, empty fault report) turned out
# to follow a degraded GNOME/mutter session; a fresh login clears it. A
# r.Vulkan.DelayAcquireBackBuffer=0 workaround in the engine-local
# ConsoleVariables.ini was retired the same day: it made the editor present
# alternating black frames ("the editor flashes") under this driver/PRIME.
# If startup device-lost returns: log out/in first; the cvar (still there,
# commented) is a last-resort stopgap that trades crashes for flicker.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UE_ROOT="${UE_ROOT:-$HOME/UnrealEngine}"
NVIDIA_ICD="${NVIDIA_ICD:-/usr/share/vulkan/icd.d/nvidia_icd.json}"

if [[ ! -f "$NVIDIA_ICD" ]]; then
  echo "warning: $NVIDIA_ICD not found; launching without the ICD pin" >&2
  exec env __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia \
    "$UE_ROOT/Engine/Binaries/Linux/UnrealEditor" \
    "$REPO_ROOT/unreal/SmokeEmIfYouGotEm.uproject" \
    -nop4 -DisableAsyncCompute -vulkanpresentmode=2 -norhithread "$@"
fi

exec env \
  VK_DRIVER_FILES="$NVIDIA_ICD" \
  __NV_PRIME_RENDER_OFFLOAD=1 \
  __VK_LAYER_NV_optimus=NVIDIA_only \
  __GLX_VENDOR_LIBRARY_NAME=nvidia \
  "$UE_ROOT/Engine/Binaries/Linux/UnrealEditor" \
  "$REPO_ROOT/unreal/SmokeEmIfYouGotEm.uproject" \
  -nop4 -DisableAsyncCompute -vulkanpresentmode=2 -norhithread "$@"
