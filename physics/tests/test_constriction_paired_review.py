"""Source-extension play must retain the strict native evidence contract."""
import copy
import subprocess
import sys
from pathlib import Path

import pytest
from prepare_constriction_paired_review import verify_union_evidence


@pytest.fixture
def evidence():
    revision={'schema':'source-supported'}
    assets={role:dict(native_source_sha256=role,triangle_count=count)
            for role,count in [('installed',803842),('candidate',803842),('cap',6404)]}
    geometry=dict(terrain_revision=revision,terrain_union=dict(terrain_revision=revision))
    probes=dict(schema='raftsim.constriction_installed_union_probes.v1',terrain_revision=revision,
                assets=assets,translation_cm=[-543186.,-360044.,0.])
    collision=dict(terrain_revision=revision,assets=copy.deepcopy(assets),failures=[],
        sampled_full_map_union_verified=True,hydraulic_state_verified=True,
        fresh_saved_candidate_reload_verified=True,position_tolerance_cm=.1,
        saved_assets=False,saved_levels=False,duplicate_ground_added=False,
        candidate_translation_cm=probes['translation_cm'],
        native_sources={role:dict(available=True,allow_cpu_access=True,
            collision_source_sha256=asset['native_source_sha256'],triangle_count=asset['triangle_count'])
            for role,asset in assets.items()})
    return geometry,probes,collision


def test_matching_source_collision_and_water(evidence):
    verify_union_evidence(*evidence)


@pytest.mark.parametrize('key,value',[
    ('terrain_revision',{}),('assets',{}),('failures',[{}]),('sampled_full_map_union_verified',False),
    ('hydraulic_state_verified',False),('fresh_saved_candidate_reload_verified',False),
    ('position_tolerance_cm',1.),('saved_assets',True),('saved_levels',True),
    ('duplicate_ground_added',True),('candidate_translation_cm',[0,0,0])])
def test_rejects_changed_native_contract(evidence,key,value):
    evidence[2][key]=value
    with pytest.raises(ValueError):verify_union_evidence(*evidence)


@pytest.mark.parametrize('role',['installed','candidate','cap'])
@pytest.mark.parametrize('key,value',[
    ('available',False),('allow_cpu_access',False),('collision_source_sha256','other'),('triangle_count',1)])
def test_rejects_incomplete_native_mesh_evidence(evidence,role,key,value):
    evidence[2]['native_sources'][role][key]=value
    with pytest.raises(ValueError):verify_union_evidence(*evidence)


def test_preplay_validator_imports_without_numpy():
    scripts=Path(__file__).resolve().parents[1]/'scripts'
    code="import sys; sys.path.insert(0,sys.argv[1]); import prepare_constriction_paired_review; assert 'numpy' not in sys.modules"
    subprocess.run([sys.executable,'-S','-c',code,str(scripts)],check=True,capture_output=True,text=True)
