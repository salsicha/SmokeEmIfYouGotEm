"""Apply the paired Pinball terrain/cook patch in the existing normal map.

Run in a fresh editor with RAFTSIM_PINBALL_EXPORT and RAFTSIM_PINBALL_RECEIPT.
After Unreal exits, finish_pinball_reference_install.py completes the paired
runtime files. Never truncate arrays while Unreal may have them memory mapped.
The source comparison refuses overlapping user edits. Only the small terrain
delta and its explicitly paired runtime files are saved; no scene regeneration.
"""
import hashlib
import json
import os
import shutil
from pathlib import Path
import unreal

ROOT=Path(__file__).resolve().parents[2]
RIVER=ROOT/'physics/data/real_world/pacuare_river_costa_rica'
PACKAGE=RIVER/'scenario_huacas_evidence_2017'
TERRAIN=RIVER/'terrain/huacas_evidence_2017'
LEVEL='/Game/RaftSim/Maps/L_UpperHuacas'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source=(ROOT/os.environ['RAFTSIM_PINBALL_EXPORT']).resolve()
    receipt=(ROOT/os.environ['RAFTSIM_PINBALL_RECEIPT']).resolve()
    assert receipt.is_relative_to(ROOT/'tmp') and not receipt.exists()
    assert source.is_relative_to(ROOT/'tmp')
    assert (source/'export.json').exists()
    manifest=json.loads((source/'cooked_flow_fields/manifest.json').read_text())
    provenance=manifest['pinball_reference']
    assert sha(PACKAGE/'cooked_flow_fields/manifest.json')==provenance['cooked_manifest_sha256']
    before=TERRAIN/'huacas_evidence_heightfield_2017.png'
    after=source/before.name
    assert sha(before)==provenance['source_heightfield_sha256']
    assert sha(after)==provenance['candidate_heightfield_sha256']
    assert sha(ROOT/provenance['catalogue'])==provenance['catalogue_sha256']
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(LEVEL)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    landscapes=[a for a in actors if isinstance(a,unreal.Landscape)]
    assert len(landscapes)==1,'Expected the single existing Pacuare Landscape'
    landscape=landscapes[0]
    assert landscape.get_package().get_name()==LEVEL,'External terrain packages require an explicit save inventory'
    mapfile=ROOT/'unreal/Content/RaftSim/Maps/L_UpperHuacas.umap'
    backup=receipt.with_suffix('')
    assert not backup.exists()
    backup.mkdir(parents=True)
    shutil.copy2(mapfile,backup/mapfile.name)
    mapping={}
    for folder in ('cooked_flow_fields','scenario'):
        for staged in (source/folder).rglob('*'):
            if staged.is_file():mapping[PACKAGE/folder/staged.relative_to(source/folder)]=staged
    mapping[PACKAGE/'runtime/moving_water_streaming.json']=source/'moving_water_streaming.json'
    mapping[before]=after
    mapping[TERRAIN/'huacas_evidence_terrain_manifest.json']=source/'huacas_evidence_terrain_manifest.json'
    changed={}
    for live,staged in mapping.items():
        assert live.exists(),'No implicit new runtime paths'
        if sha(live)==sha(staged):continue
        relative=live.relative_to(ROOT)
        copy=backup/relative;copy.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(live,copy)
        changed[relative.as_posix()]={'before':sha(live),'after':sha(staged),
                                     'staged':staged.relative_to(ROOT).as_posix()}
    patch=json.loads(unreal.RaftSimLandscapePatchLibrary.apply_heightfield_patch(landscape,str(before),str(after)))
    assert patch['applied'] and patch['collision_rebuilt'],patch
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    # Terrain textures/collision are subobjects in this non-partitioned map.
    assert unreal.EditorLoadingAndSavingUtils.save_packages([landscape.get_package()],False)
    report=dict(schema='raftsim.pinball_reference_install.v1',level=LEVEL,patch=patch,
                map_sha256_before=sha(backup/mapfile.name),map_sha256_after=sha(mapfile),
                paired_runtime_files=changed,backup=str(backup.relative_to(ROOT)),
                status='map_saved_runtime_pending',final_receipt=receipt.relative_to(ROOT).as_posix(),
                acceptance='Installed for native validation; not yet accepted or a performance claim')
    receipt.with_suffix('.pending.json').write_text(json.dumps(report,indent=2)+'\n')
    unreal.log('RAFTSIM_PINBALL_MAP_PREPARED '+json.dumps(report))


if __name__=='__main__':main()
