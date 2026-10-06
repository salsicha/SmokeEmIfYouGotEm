#!/usr/bin/env bash
# Install the repo's git hooks (currently: the locked-source commit gate).
# Any commit that stages a hash-locked source must refresh its review locks
# and pass the full physics suite (release-1.0-plan.md testing rule).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$REPO_ROOT/.git/hooks/pre-commit"

cat > "$HOOK" <<'EOF'
#!/usr/bin/env bash
exec python3 "$(git rev-parse --show-toplevel)/Scripts/check_locked_source_gate.py" --staged
EOF
chmod +x "$HOOK"
echo "Installed pre-commit locked-source gate: $HOOK"
echo "Bypass consciously with RAFTSIM_SKIP_LOCKED_GATE=1 or git commit --no-verify."
