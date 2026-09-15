"""Shared source bed, actual full-map collision and native candidate loader."""
from pathlib import Path
import json
import os
import sys
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from verify_south_fork_rock_union_collision import main
from verify_troublemaker_dem_rock_cap_collision import candidate_configuration


def runtime_configuration(path,root=ROOT):
    root=Path(root).resolve();config=candidate_configuration(path,root)
    raw=json.loads(Path(path).read_text())
    expected=(root/raw['runtime_expectations']).resolve()
    if not expected.is_relative_to(root/'tmp') or not expected.is_file():
        raise ValueError('Existing generated local runtime expectations required')
    return config|dict(runtime_expectations=expected)

if __name__=='__main__':
    try:
        config_path=os.environ.get('RAFTSIM_ROCK_COLLISION_CONFIG')
        if config_path:
            config=runtime_configuration(config_path)
            main(config['runtime_expectations'],output=config['report'],probe_path=config['probes'],
                export_directory=config['export_directory'],asset_path=config['asset'])
        else:
            main(ROOT/'tmp/south-fork-rock-union-runtime-expectations-v2-20260915.json',
                ROOT/'unreal/Saved/RaftSimValidation/south-fork-rock-union-runtime-v2-20260915.json')
    finally:unreal.SystemLibrary.quit_editor()
