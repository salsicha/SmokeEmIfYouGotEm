#!/bin/zsh
# Build, sign, exercise, archive, and checksum the macOS Apple Silicon RC.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RC_ROOT="${1:-/private/tmp/RaftSim-1.0.0-rc1-macos}"
PACKAGE_ROOT="$RC_ROOT/package"
ARTIFACT_ROOT="$RC_ROOT/artifacts"
APP=""
EXECUTABLE=""

assert_no_competing_unreal_processes() {
  local phase="$1"
  local competing_processes
  competing_processes="$(
    ps -axo pid=,ucomm=,command= | awk '
      $2 == "UnrealEditor" || $2 == "UnrealEditor-Cmd" ||
      $2 ~ /^SmokeEmIfYouGotEm/ { print }
    '
  )"
  if [[ -n "$competing_processes" ]]; then
    echo "Release qualification requires an isolated Unreal/GPU session ($phase)." >&2
    echo "$competing_processes" >&2
    exit 16
  fi
}

assert_no_competing_unreal_processes "before packaging"
mkdir -p "$PACKAGE_ROOT" "$ARTIFACT_ROOT"
"$REPO_ROOT/unreal/Scripts/package_mac.sh" Shipping "$PACKAGE_ROOT"

APP="$(find "$PACKAGE_ROOT/Mac" -maxdepth 1 -name '*.app' -print -quit)"
if [[ -z "$APP" ]]; then
  echo "Archived macOS application was not found." >&2
  exit 9
fi
EXECUTABLE_NAME="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$APP/Contents/Info.plist")"
EXECUTABLE="$APP/Contents/MacOS/$EXECUTABLE_NAME"

SIGN_IDENTITY="${RAFTSIM_MAC_SIGN_IDENTITY:-}"
SIGNATURE_POLICY="${RAFTSIM_MAC_SIGNATURE_POLICY:-any-valid}"
TIMESTAMP_ARGS=(--timestamp=none)
if [[ "$SIGNATURE_POLICY" == "distribution" ]]; then
  # Developer ID notarization requires a trusted signing timestamp. Local
  # development and ad-hoc preflights stay deterministic and network-free.
  TIMESTAMP_ARGS=(--timestamp)
fi
if [[ -z "$SIGN_IDENTITY" ]]; then
  SIGN_IDENTITY="$(security find-identity -v -p codesigning | sed -n 's/.*"\(.*\)"/\1/p' | head -1)"
fi
if [[ -z "$SIGN_IDENTITY" ]]; then
  # Local RCs remain executable and verifiable with an ad-hoc signature. The
  # tracked manifest keeps notarization blocked until Developer ID credentials
  # are available on the release runner.
  SIGN_IDENTITY="-"
fi

# UE may stage third-party dylibs with ad-hoc signatures even when Xcode signs
# the outer application with a development/distribution team. macOS rejects a
# mixed-Team process at load time, so align every nested runtime binary first.
while IFS= read -r -d '' NESTED_BINARY; do
  codesign --force --sign "$SIGN_IDENTITY" --options runtime \
    "${TIMESTAMP_ARGS[@]}" "$NESTED_BINARY"
done < <(find "$APP/Contents/UE" -type f -name '*.dylib' -print0)
codesign --force --deep --sign "$SIGN_IDENTITY" --options runtime \
  "${TIMESTAMP_ARGS[@]}" \
  --entitlements "$REPO_ROOT/unreal/Build/Mac/Resources/Sandbox.NoNet.entitlements" "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"

RAPID_LOG="$ARTIFACT_ROOT/packaged_rapid_regression.log"
QA_LOG="$ARTIFACT_ROOT/release_candidate_qa.log"
FRESH_PROFILE_LOG="$ARTIFACT_ROOT/fresh_profile_first_run.log"
PERFORMANCE_LOG="$ARTIFACT_ROOT/full_reach_performance_soak.log"

"$EXECUTABLE" -RaftSimPackagedRegression \
  -RaftSimValidationStdout \
  -NullRHI -NoSound -Unattended -stdout -FullStdOutLogOutput 2>&1 | tee "$RAPID_LOG"
python3 "$REPO_ROOT/Scripts/release_candidate.py" extract-qa-log \
  --log "$RAPID_LOG" --output "$ARTIFACT_ROOT/packaged_rapid_regression.json"

"$EXECUTABLE" -RaftSimReleaseCandidateQA \
  -RaftSimValidationStdout \
  -NullRHI -NoSound -Unattended -stdout -FullStdOutLogOutput 2>&1 | tee "$QA_LOG"
python3 "$REPO_ROOT/Scripts/release_candidate.py" extract-qa-log \
  --log "$QA_LOG" --output "$ARTIFACT_ROOT/release_candidate_qa.json"

# The signed app is sandboxed, so an arbitrary /private/tmp UserDir can create
# defaults in memory but cannot persist them. Give this RC a unique directory
# inside its own writable container and fail rather than reusing prior state.
BUNDLE_IDENTIFIER="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP/Contents/Info.plist")"
FRESH_PROFILE_RUN_ID="$(basename "$RC_ROOT")"
FRESH_PROFILE_ROOT="$HOME/Library/Containers/$BUNDLE_IDENTIFIER/Data/tmp/RaftSimQA-$FRESH_PROFILE_RUN_ID"
if [[ -e "$FRESH_PROFILE_ROOT" ]]; then
  echo "Fresh-profile QA requires a new, unused user directory: $FRESH_PROFILE_ROOT" >&2
  exit 14
fi
# Let the sandboxed application create its own UserDir. Host-side mkdir can
# block on macOS container-manager privacy checks even though the signed app
# itself has immediate write authority inside this path.
"$EXECUTABLE" -RaftSimFreshProfileQA \
  -UserDir="$FRESH_PROFILE_ROOT" \
  -RaftSimValidationStdout \
  -NullRHI -NoSound -Unattended -stdout -FullStdOutLogOutput 2>&1 | tee "$FRESH_PROFILE_LOG"
python3 "$REPO_ROOT/Scripts/release_candidate.py" extract-qa-log \
  --log "$FRESH_PROFILE_LOG" --output "$ARTIFACT_ROOT/fresh_profile_first_run.json"

PERF_SECONDS="${RAFTSIM_RC_PERF_SECONDS:-30}"
WARMUP_SECONDS="${RAFTSIM_RC_WARMUP_SECONDS:-10}"
PERF_PROTOCOL="${RAFTSIM_RC_PERF_PROTOCOL:-windowed}"
case "$PERF_PROTOCOL" in
  windowed)
    PERF_RENDER_ARGS=(-Windowed)
    ;;
  offscreen-diagnostic)
    PERF_RENDER_ARGS=(-RenderOffScreen)
    ;;
  *)
    echo "RAFTSIM_RC_PERF_PROTOCOL must be windowed or offscreen-diagnostic." >&2
    exit 15
    ;;
esac
assert_no_competing_unreal_processes "before the player-presentation performance soak"
"$EXECUTABLE" \
  -UserDir="$FRESH_PROFILE_ROOT" \
  -RaftSimPerformanceSoakSeconds="$PERF_SECONDS" \
  -RaftSimPerformanceWarmupSeconds="$WARMUP_SECONDS" \
  -RaftSimPerformanceTravelMap=/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach \
  -RaftSimPerformanceRequiredMap=L_SouthForkAmerican_FullReach \
  -RaftSimPerformanceScreenPercentage=60 \
  -RaftSimPerformanceViewDistanceQuality=2 \
  -RaftSimPerformanceAntiAliasingQuality=2 \
  -RaftSimPerformanceGlobalIlluminationQuality=2 \
  -RaftSimPerformanceReflectionQuality=2 \
  -RaftSimPerformanceShadowQuality=2 \
  -RaftSimPerformancePostProcessQuality=2 \
  -RaftSimPerformanceTextureQuality=2 \
  -RaftSimPerformanceEffectsQuality=2 \
  -RaftSimPerformanceFoliageQuality=2 \
  -RaftSimPerformanceShadingQuality=2 \
  -RaftSimPerformanceAntiAliasingMethod=4 \
  -RaftSimPerformanceBloomQuality=5 \
  -RaftSimPerformanceSkeletalMeshLodBias=0 \
  -RaftSimPerformanceLumenTranslucencyRadianceCacheEnabled=0 \
  -RaftSimPerformanceNaniteEnabled=1 \
  -RaftSimPerformanceVolumetricCloudEnabled=1 \
  -ExecCmds="Scalability 2" \
  -unattended -NoSound "${PERF_RENDER_ARGS[@]}" -ForceRes -ResX=1920 -ResY=1080 \
  -RaftSimValidationStdout \
  -stdout -FullStdOutLogOutput 2>&1 | tee "$PERFORMANCE_LOG"
python3 "$REPO_ROOT/Scripts/release_candidate.py" extract-qa-log \
  --log "$PERFORMANCE_LOG" --output "$ARTIFACT_ROOT/full_reach_performance_soak.json"

if [[ "$SIGNATURE_POLICY" == "distribution" ]]; then
  if [[ "$SIGN_IDENTITY" != *"Developer ID Application"* ]]; then
    echo "A Developer ID Application identity is required for distribution signing." >&2
    exit 12
  fi
  NOTARY_PROFILE="${RAFTSIM_NOTARY_PROFILE:-}"
  if [[ -z "$NOTARY_PROFILE" ]]; then
    echo "RAFTSIM_NOTARY_PROFILE is required for notarized distribution RCs." >&2
    exit 13
  fi
  NOTARY_SUBMISSION="$RC_ROOT/notary-submission.zip"
  ditto -c -k --sequesterRsrc --keepParent "$APP" "$NOTARY_SUBMISSION"
  xcrun notarytool submit "$NOTARY_SUBMISSION" \
    --keychain-profile "$NOTARY_PROFILE" --wait
  xcrun stapler staple "$APP"
  codesign --verify --deep --strict --verbose=2 "$APP"
  spctl --assess --type execute --verbose=2 "$APP"
fi

DIRTY_FLAG=()
if [[ "${RAFTSIM_ALLOW_DIRTY_RC:-0}" == "1" ]]; then
  DIRTY_FLAG=(--allow-dirty)
fi
python3 "$REPO_ROOT/Scripts/release_candidate.py" finalize \
  --platform macos \
  --package-root "$APP" \
  --output-dir "$ARTIFACT_ROOT" \
  --configuration Shipping \
  --signature-policy "$SIGNATURE_POLICY" \
  --qa-report "$ARTIFACT_ROOT/packaged_rapid_regression.json" \
  --qa-report "$ARTIFACT_ROOT/release_candidate_qa.json" \
  --qa-report "$ARTIFACT_ROOT/fresh_profile_first_run.json" \
  --qa-report "$ARTIFACT_ROOT/full_reach_performance_soak.json" \
  "${DIRTY_FLAG[@]}"

VERIFY_POLICY_FLAGS=()
if [[ "${RAFTSIM_ALLOW_DIRTY_RC:-0}" == "1" ]]; then
  VERIFY_POLICY_FLAGS+=(--allow-dirty)
fi
if [[ "$SIGNATURE_POLICY" != "distribution" ]]; then
  VERIFY_POLICY_FLAGS+=(--allow-nondistribution)
fi
python3 "$REPO_ROOT/Scripts/release_candidate.py" verify-artifact \
  --manifest "$ARTIFACT_ROOT/macos-arm64-release-manifest.json" \
  --artifact-dir "$ARTIFACT_ROOT" \
  --platform macos \
  --output "$ARTIFACT_ROOT/macos-arm64-release-verification.json" \
  "${VERIFY_POLICY_FLAGS[@]}"

echo "Mac RC artifacts: $ARTIFACT_ROOT"
