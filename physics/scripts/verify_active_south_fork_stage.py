"""Validate the South Fork bundle selected by the build, never a stale default.

This checks the actual staged tree without copying or repairing its files.
It does not validate a cooked game executable or accept the physical state.
"""
import argparse
import json
from pathlib import Path
import re

from package_runtime_bundle import logical_path, verify_staged

ROOT = Path(__file__).resolve().parents[2]
RULES = 'unreal/Plugins/RaftSim/Source/RaftSimWater/RaftSimWater.Build.cs'


def selected_bundle(root):
    root = Path(root).resolve()
    rules = (root / RULES).read_text()
    # Remove comments so a historical call cannot masquerade as an active one.
    rules = re.sub(r'/\*.*?\*/|//[^\n]*', '', rules, flags=re.DOTALL)
    calls = re.findall(r'StageVerifiedRuntimeBundle\s*\(\s*RepoRoot\s*,\s*"([^"]+)"\s*,\s*RuntimeDestinations\s*\)', rules)
    if len(calls) != 1:
        raise ValueError('Exactly one explicit runtime bundle selection required in build rules')
    relative = logical_path(calls[0])
    if not relative.startswith('physics/data/runtime_bundles/south_fork_'):
        raise ValueError('Expected a South Fork runtime bundle')
    bundle = (root / relative).resolve()
    if not bundle.is_relative_to(root):
        raise ValueError('Bundle escapes repository')
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--staged-root', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('Fresh report required')
    if args.staged_root.resolve() == args.root.resolve():
        parser.error('An actual staged tree, not the source root, is required')
    bundle = selected_bundle(args.root)
    try:
        result = verify_staged(bundle, args.staged_root)
    except (OSError, ValueError, KeyError) as error:
        result = dict(passed=False, error=str(error), physical_acceptance=False,
                      packaged_execution_verified=False)
    result['selected_bundle'] = bundle.relative_to(args.root.resolve()).as_posix()
    result['staged_root'] = str(args.staged_root.resolve())
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
