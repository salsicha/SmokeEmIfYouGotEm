#!/bin/bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <downloaded-windows-artifact-directory>" >&2
  exit 2
fi
command -v proton >/dev/null || { echo "proton command is required" >&2; exit 3; }

ARTIFACT_DIR="$1"
MANIFEST="$ARTIFACT_DIR/windows-x64-release-manifest.json"
ARCHIVE="$ARTIFACT_DIR/RaftSim-1.0.0-rc1-windows-x64.zip"
[[ -f "$MANIFEST" ]] || { echo "Windows RC manifest missing" >&2; exit 4; }
[[ -f "$ARCHIVE" ]] || { echo "Windows RC archive missing" >&2; exit 5; }
python3 Scripts/release_candidate.py verify-artifact \
  --manifest "$MANIFEST" --artifact-dir "$ARTIFACT_DIR" --platform windows \
  --output "$ARTIFACT_DIR/windows-x64-proton-input-verification.json"
WORK_ROOT="$(mktemp -d)"
trap 'rm -rf "$WORK_ROOT"' EXIT
unzip -q "$ARCHIVE" -d "$WORK_ROOT"
EXE="$(find "$WORK_ROOT" -name 'SmokeEmIfYouGotEm.exe' -print -quit)"
[[ -n "$EXE" ]] || { echo "Windows executable missing" >&2; exit 6; }

export STEAM_COMPAT_DATA_PATH="$WORK_ROOT/proton-prefix"
PROTON_LOG="$ARTIFACT_DIR/proton-release-candidate.log"
timeout 120 proton run "$EXE" -RaftSimReleaseCandidateQA \
  -RaftSimValidationStdout \
  -NullRHI -NoSound -Unattended -stdout -FullStdOutLogOutput 2>&1 | tee "$PROTON_LOG"
python3 Scripts/release_candidate.py extract-qa-log \
  --log "$PROTON_LOG" --output "$ARTIFACT_DIR/proton_release_candidate_qa.json"
python3 - "$ARTIFACT_DIR/proton_release_candidate_qa.json" "$ARTIFACT_DIR/proton-smoke.json" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if report.get("passed") is not True:
    raise SystemExit("Proton packaged QA did not pass")
summary = {
    "schema": "raftsim.m9.proton_smoke.v1",
    "release_candidate_qa": report.get("schema"),
    "passed": True,
}
Path(sys.argv[2]).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
PY
