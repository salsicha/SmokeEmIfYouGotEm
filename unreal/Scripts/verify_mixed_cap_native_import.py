"""Transient native identity check of the mixed-source cap; no saved assets."""
import json
import os
from pathlib import Path
import sys
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from verify_troublemaker_dem_rock_cap_collision import import_candidate_solid


def main():
    config=json.loads((ROOT/os.environ['RAFTSIM_MIXED_CAP_IMPORT_CONFIG']).read_text())
    output=(ROOT/config['report']).resolve()
    export=(ROOT/config['export_directory']).resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp') or not export.is_relative_to(ROOT/'tmp'):
        raise ValueError('Fresh local report and local export required')
    asset='/Game/RaftSim/Environment/GeneratedLocalReview/MixedCap20260925/SM_OriginalReturnRockSolid'
    mesh,receipt=import_candidate_solid(export,asset)
    native=json.loads(unreal.RaftSimGroundSourceLibrary.audit_collision_source(mesh))
    passed=(native['available'] and native['allow_cpu_access'] and native['collision_lod']==0
            and native['collision_source_sha256']==config['expected_native_source_sha256']
            and native['triangle_count']==receipt['triangle_count']==6428)
    output.write_text(json.dumps(dict(passed=passed,native=native,
        expected_native_source_sha256=config['expected_native_source_sha256'],
        fbx_sha256=receipt['fbx_sha256'],source_cap_sha256=receipt['source_cap_sha256'],
        saved_assets=False,saved_levels=False,full_map_collision_verified=False,
        playable_integrated=False,visual_acceptance=False),indent=2)+'\n')
    assert passed,'Imported native source differs from exact candidate: '+str(output)
    unreal.log('Mixed cap native identity verified: '+str(output))


if __name__=='__main__':
    try:main()
    except Exception:
        import traceback
        config=json.loads((ROOT/os.environ['RAFTSIM_MIXED_CAP_IMPORT_CONFIG']).read_text())
        failure=(ROOT/config['report']).with_suffix('.failure.json')
        if not failure.exists():failure.write_text(json.dumps(dict(passed=False,error=traceback.format_exc()),indent=2)+'\n')
        raise
    finally:unreal.SystemLibrary.quit_editor()
