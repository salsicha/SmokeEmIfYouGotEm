"""Read-only proof that editor Python and its toolset bindings remain available."""
import argparse
import json
from pathlib import Path

import unreal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--quit-editor', action='store_true')
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    required = ('AgentSkill', 'PythonTestRunner', 'EditorAssetSubsystem')
    missing = [name for name in required if not hasattr(unreal, name)]
    if missing:
        raise RuntimeError(f'Editor Python bindings missing: {missing}')
    subsystem = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    if subsystem is None:
        raise RuntimeError('Actual editor asset subsystem unavailable')
    import toolset_registry.tests
    if toolset_registry.tests._toolset_registry_test_runner is None:
        raise RuntimeError('Toolset startup did not register its Python test runner')
    report = dict(schema='raftsim.editor_python_startup.v1', passed=True,
                  engine_version=unreal.SystemLibrary.get_engine_version(),
                  required_bindings=list(required), editor_asset_subsystem=True,
                  toolset_startup_runner=True, asset_mutations=False)
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    unreal.log('RAFTSIM_EDITOR_PYTHON_STARTUP_PASS ' + str(args.report))
    if args.quit_editor:
        unreal.SystemLibrary.quit_editor()


if __name__ == '__main__':
    main()
