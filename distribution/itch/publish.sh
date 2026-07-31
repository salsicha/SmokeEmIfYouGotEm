#!/bin/zsh
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <artifact.zip> <owner/game:channel>" >&2
  exit 2
fi

ARTIFACT="$1"
TARGET="$2"
SUMS="${ARTIFACT:h}/SHA256SUMS"

command -v butler >/dev/null || { echo "butler is required" >&2; exit 3; }
[[ -f "$ARTIFACT" && -f "$SUMS" ]] || { echo "artifact or SHA256SUMS missing" >&2; exit 4; }

EXPECTED="$(awk -v name="${ARTIFACT:t}" '$2 == name {print $1}' "$SUMS")"
ACTUAL="$(shasum -a 256 "$ARTIFACT" | awk '{print $1}')"
[[ -n "$EXPECTED" && "$EXPECTED" == "$ACTUAL" ]] || { echo "checksum mismatch" >&2; exit 5; }

butler push "$ARTIFACT" "$TARGET" --userversion "1.0.0-rc1"
