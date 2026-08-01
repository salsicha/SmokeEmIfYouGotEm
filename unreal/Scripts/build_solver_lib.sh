#!/usr/bin/env bash
# Build the raftsim_water static library for linking into the RaftSimWater
# module (release-1.0-plan.md §5 A-1). Output: physics/cpp/build-ue/libraftsim_water.a
#
# The archive must match the C++ runtime UE links on each platform:
#   - macOS: AppleClang + libc++ (system defaults).
#   - Linux: UE compiles with its bundled clang/libc++ toolchain, so a
#     gcc/libstdc++ archive will not link (std:: symbols mangle differently).
#     We use the toolchain under $UE_ROOT/Engine/Extras/ThirdPartyNotUE/SDKs
#     when present (same sysroot/libc++ UBT uses), else system clang -stdlib=libc++.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD_DIR="$REPO_ROOT/physics/cpp/build-ue"

CMAKE_ARGS=(
  -DCMAKE_BUILD_TYPE=Release
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON
  -DCMAKE_CXX_VISIBILITY_PRESET=hidden
)

case "$(uname -s)" in
  Darwin)
    CMAKE_ARGS+=(
      -DCMAKE_OSX_ARCHITECTURES=arm64
      -DCMAKE_OSX_DEPLOYMENT_TARGET=14.0
    )
    ;;
  Linux)
    UE_ROOT="${UE_ROOT:-$HOME/UnrealEngine}"
    TOOLCHAIN=""
    if [ -d "$UE_ROOT/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64" ]; then
      TOOLCHAIN="$(find "$UE_ROOT/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64" \
        -maxdepth 2 -type d -name 'x86_64-unknown-linux-gnu' | sort | tail -n1)"
    fi
    if [ -n "$TOOLCHAIN" ] && [ -x "$TOOLCHAIN/bin/clang++" ]; then
      echo "Using UE Linux toolchain: $TOOLCHAIN"
      CMAKE_ARGS+=(
        -DCMAKE_C_COMPILER="$TOOLCHAIN/bin/clang"
        -DCMAKE_CXX_COMPILER="$TOOLCHAIN/bin/clang++"
        -DCMAKE_C_FLAGS="--sysroot=$TOOLCHAIN"
        -DCMAKE_CXX_FLAGS="--sysroot=$TOOLCHAIN -stdlib=libc++"
        -DCMAKE_AR="$TOOLCHAIN/bin/llvm-ar"
        -DCMAKE_RANLIB="$TOOLCHAIN/bin/llvm-ranlib"
        # Only the static archive target is built; skip link checks that
        # would otherwise need the full UBT link driver setup.
        -DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY
      )
      UE_ZLIB_ROOT="$(find "$UE_ROOT/Engine/Source/ThirdParty/zlib" -maxdepth 1 -mindepth 1 -type d | sort | tail -n1)"
      if [ -n "$UE_ZLIB_ROOT" ] && [ -f "$UE_ZLIB_ROOT/include/zlib.h" ]; then
        CMAKE_ARGS+=(
          -DZLIB_INCLUDE_DIR="$UE_ZLIB_ROOT/include"
          -DZLIB_LIBRARY="$UE_ZLIB_ROOT/lib/Unix/x86_64-unknown-linux-gnu/Release/libz.a"
        )
      fi
    elif command -v clang++ >/dev/null 2>&1 \
        && echo '#include <optional>' | clang++ -stdlib=libc++ -x c++ -fsyntax-only - >/dev/null 2>&1; then
      echo "UE Linux toolchain not found; using system clang++ with libc++"
      CMAKE_ARGS+=(
        -DCMAKE_C_COMPILER=clang
        -DCMAKE_CXX_COMPILER=clang++
        -DCMAKE_CXX_FLAGS="-stdlib=libc++"
      )
    else
      echo "error: need the UE Linux toolchain (set UE_ROOT, default ~/UnrealEngine)" >&2
      echo "       or system clang++ with libc++ (e.g. apt install clang libc++-dev libc++abi-dev)." >&2
      echo "       A gcc/libstdc++ build of this archive cannot link into UE on Linux." >&2
      exit 1
    fi
    ;;
esac

cmake -S "$REPO_ROOT/physics/cpp" -B "$BUILD_DIR" "${CMAKE_ARGS[@]}"
cmake --build "$BUILD_DIR" --target raftsim_water -j

echo "Built: $BUILD_DIR/libraftsim_water.a"
